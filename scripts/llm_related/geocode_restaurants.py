import os, time, json, logging, argparse, hashlib
from typing import Optional, Tuple, Dict, Any, List
import psycopg2
import psycopg2.extras
import requests

LOG = logging.getLogger("geocode")
DEFAULT_BATCH_SLEEP = float(os.getenv("GEO_SLEEP_SEC", "0.25"))  # rate-limit
CACHE_PATH = os.getenv("GEO_CACHE_PATH", ".cache/geocode_cache.json")

def load_cache() -> Dict[str, Any]:
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_cache(cache: Dict[str, Any]) -> None:
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        LOG.warning("Failed to persist cache at %s", CACHE_PATH)

def pg_connect():
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", ""),
        dbname=os.getenv("PG_DATABASE", "postgres"),
        connect_timeout=10,
    )
    conn.autocommit = False
    return conn

def table_exists(conn, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        """, (table,))
        return cur.fetchone() is not None

def get_columns(conn, table: str) -> List[str]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s
        """, (table,))
        return [r[0] for r in cur.fetchall()]

def first_existing(cols: List[str], candidates: List[str]) -> Optional[str]:
    s = set(cols)
    for c in candidates:
        if c in s:
            return c
    return None

def pick_schema(conn):
    # Defaults; override with env if needed
    restaurants_table = os.getenv("RESTAURANTS_TABLE", "restaurants")
    res_pk = os.getenv("RESTAURANTS_PK", "res_id")
    # In this project restaurants has res_name
    res_name_col = os.getenv("RESTAURANTS_NAME_COL", "res_name")
    # Optional context columns for better geocoding
    res_city_col = os.getenv("RESTAURANTS_CITY_COL", "city")
    res_addr_col = os.getenv("RESTAURANTS_ADDR_COL", "address")

    loc_table_candidates = [os.getenv("RESTAURANT_LOCATIONS_TABLE", "restaurant_locations")]
    loc_table = None
    for t in loc_table_candidates:
        if table_exists(conn, t):
            loc_table = t
            break

    if not table_exists(conn, restaurants_table):
        raise RuntimeError(f"Table not found: {restaurants_table}. Set RESTAURANTS_TABLE env.")

    rcols = get_columns(conn, restaurants_table)

    # Case A: separate restaurant_locations table exists
    if loc_table:
        lcols = get_columns(conn, loc_table)
        # Column names based on entities: latitude, longitude, location_name, address, rl_id, res_id
        lat_col = first_existing(lcols, [os.getenv("RESTAURANT_LOC_LAT_COL", "latitude"), "lat","y"])
        lng_col = first_existing(lcols, [os.getenv("RESTAURANT_LOC_LNG_COL", "longitude"), "lng","lon","x"])
        if not lat_col or not lng_col:
            raise RuntimeError(f"{loc_table} missing lat/lng columns. Found: {lcols}")
        loc_pk_col = first_existing(lcols, [os.getenv("RESTAURANT_LOC_PK", "rl_id")])
        loc_fk_col = first_existing(lcols, [os.getenv("RESTAURANT_LOC_FK", res_pk), "res_id", "restaurant_id"])
        if not loc_fk_col:
            raise RuntimeError(f"{loc_table} missing FK to restaurants (tried env RESTAURANT_LOC_FK / {res_pk}/res_id/restaurant_id)")
        return {
            "mode": "separate",
            "restaurants_table": restaurants_table,
            "res_pk": res_pk,
            "res_name_col": res_name_col if res_name_col in rcols else None,
            "res_city_col": res_city_col if res_city_col in rcols else None,
            "res_addr_col": res_addr_col if res_addr_col in rcols else None,
            "loc_table": loc_table,
            "loc_pk": loc_pk_col,  # rl_id (may be None for missing rows)
            "loc_fk": loc_fk_col,  # res_id
            "lat_col": lat_col,
            "lng_col": lng_col,
            "loc_name_col": first_existing(lcols, [os.getenv("RESTAURANT_LOC_NAME_COL", "location_name"), "name"]),
            "loc_addr_col": first_existing(lcols, [os.getenv("RESTAURANT_LOC_ADDR_COL", "address"), "formatted_address"]),
            "addr_store_col": first_existing(lcols, ["formatted_address","address"]),
            "place_id_col": first_existing(lcols, ["place_id"]),
            "source_col": first_existing(lcols, ["source","provider"]),
        }

    # Case B: lat/lng lives on restaurants
    lat_col = first_existing(rcols, ["lat","latitude","y"])
    lng_col = first_existing(rcols, ["lng","lon","longitude","x"])
    if not lat_col or not lng_col:
        raise RuntimeError(
            "No restaurant_locations table and restaurants has no lat/lng columns. "
            "Set env vars or create columns."
        )
    return {
        "mode": "inline",
        "restaurants_table": restaurants_table,
        "res_pk": res_pk,
        "res_name_col": res_name_col if res_name_col in rcols else None,
        "res_city_col": res_city_col if res_city_col in rcols else None,
        "res_addr_col": res_addr_col if res_addr_col in rcols else None,
        "lat_col": lat_col,
        "lng_col": lng_col,
        "addr_store_col": first_existing(rcols, ["formatted_address","geocoded_address","address"]),
        "place_id_col": first_existing(rcols, ["place_id"]),
        "source_col": first_existing(rcols, ["geo_source","geo_provider"]),
    }

def select_missing(conn, sch, limit: Optional[int], offset: Optional[int]):
    t = sch["restaurants_table"]; pk = sch["res_pk"]
    name = sch["res_name_col"]; city = sch["res_city_col"]; addr = sch["res_addr_col"]

    if sch["mode"] == "separate":
        lt = sch["loc_table"]; fk = sch["loc_fk"]; lat=sch["lat_col"]; lng=sch["lng_col"]
        rlpk = sch.get("loc_pk"); loc_name = sch.get("loc_name_col"); loc_addr = sch.get("loc_addr_col")
        # Return per-location rows (including those with no existing location row)
        sql = f"""
            SELECT rl.{rlpk} AS rl_id,
                   r.{pk}    AS res_id,
                   {('r.'+name) if name else 'NULL'}    AS res_name,
                   {('rl.'+loc_name) if loc_name else 'NULL'} AS location_name,
                   {('rl.'+loc_addr) if loc_addr else 'NULL'} AS loc_address,
                   {('r.'+addr) if addr else 'NULL'}    AS res_address,
                   {('r.'+city) if city else 'NULL'}    AS city
            FROM {t} r
            LEFT JOIN {lt} rl ON rl.{fk} = r.{pk}
            WHERE rl.{fk} IS NULL
               OR rl.{lat} IS NULL OR rl.{lng} IS NULL
               OR rl.{lat} = 0 OR rl.{lng} = 0
            ORDER BY r.{pk}, rl.{rlpk} NULLS FIRST
        """
    else:
        lat=sch["lat_col"]; lng=sch["lng_col"]
        sql = f"""
            SELECT NULL AS rl_id,
                   r.{pk} AS res_id,
                   {('r.'+name) if name else 'NULL'} AS res_name,
                   NULL AS location_name,
                   {('r.'+addr) if addr else 'NULL'} AS loc_address,
                   {('r.'+addr) if addr else 'NULL'} AS res_address,
                   {('r.'+city) if city else 'NULL'} AS city
            FROM {t} r
            WHERE r.{lat} IS NULL OR r.{lng} IS NULL OR r.{lat} = 0 OR r.{lng} = 0
            ORDER BY r.{pk}
        """
    if limit is not None:
        sql += " LIMIT %s"
        if offset is not None:
            sql += " OFFSET %s"

    with conn.cursor() as cur:
        if limit is not None and offset is not None:
            cur.execute(sql, (limit, offset))
        elif limit is not None:
            cur.execute(sql, (limit,))
        else:
            cur.execute(sql)
        return cur.fetchall()

def gm_geocode(address: str, key: str) -> Optional[Dict[str, Any]]:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    r = requests.get(url, params={"address": address, "key": key}, timeout=15)
    if r.status_code != 200:
        return None
    data = r.json()
    if data.get("status") not in ("OK","ZERO_RESULTS"):
        LOG.warning(
            "Google Geocoding API status=%s error_message=%s for address='%s'",
            data.get("status"), data.get("error_message"), address,
        )
    if data.get("status") != "OK":
        return None
    res = data["results"][0]
    loc = res["geometry"]["location"]
    return {
        "lat": loc["lat"],
        "lng": loc["lng"],
        "formatted_address": res.get("formatted_address"),
        "place_id": res.get("place_id"),
        "provider": "google",
    }

def osm_geocode(address: str, ua: str) -> Optional[Dict[str, Any]]:
    url = "https://nominatim.openstreetmap.org/search"
    r = requests.get(url, params={"q": address, "format": "json", "limit": 1}, headers={"User-Agent": ua}, timeout=15)
    if r.status_code != 200:
        return None
    arr = r.json()
    if not arr:
        return None
    item = arr[0]
    return {
        "lat": float(item["lat"]),
        "lng": float(item["lon"]),
        "formatted_address": item.get("display_name"),
        "place_id": item.get("osm_id"),
        "provider": "nominatim",
    }

def geocode(address: str, cache: Dict[str, Any], key: Optional[str], ua: str) -> Optional[Dict[str, Any]]:
    k = hashlib.sha1(address.strip().lower().encode("utf-8")).hexdigest()
    if k in cache:
        return cache[k]
    result = None
    if key:
        result = gm_geocode(address, key)
    if not result:
        result = osm_geocode(address, ua)
    if result:
        cache[k] = result
    return result

def upsert_location(conn, sch, rl_id: Optional[Any], res_id: Any, lat: float, lng: float, addr: Optional[str], place_id: Optional[str], provider: str, inferred_loc_name: Optional[str]=None):
    if sch["mode"] == "separate":
        lt, fk = sch["loc_table"], sch["loc_fk"]
        latc, lngc = sch["lat_col"], sch["lng_col"]
        addr_c, pid_c, src_c = sch["addr_store_col"], sch["place_id_col"], sch["source_col"]
        loc_name_c = sch.get("loc_name_col")

        if rl_id is not None:
            # Update this specific location row
            sets = [f"{latc}=%s", f"{lngc}=%s"]
            vals = [lat, lng]
            if addr_c: sets.append(f"{addr_c}=%s"); vals.append(addr)
            if pid_c: sets.append(f"{pid_c}=%s"); vals.append(place_id)
            if src_c: sets.append(f"{src_c}=%s"); vals.append(provider)
            sql = f"UPDATE {lt} SET {', '.join(sets)} WHERE {sch['loc_pk']}=%s"
            vals.append(rl_id)
            with conn.cursor() as cur:
                cur.execute(sql, vals)
        else:
            # No location row exists yet for this restaurant; insert a new one
            cols = [fk, latc, lngc]
            vals = [res_id, lat, lng]
            if loc_name_c and inferred_loc_name:
                cols.append(loc_name_c); vals.append(inferred_loc_name)
            if addr_c: cols.append(addr_c); vals.append(addr)
            if pid_c: cols.append(pid_c); vals.append(place_id)
            if src_c: cols.append(src_c); vals.append(provider)
            cols_sql = ", ".join(cols)
            placeholders = ", ".join(["%s"] * len(vals))
            sql = f"INSERT INTO {lt} ({cols_sql}) VALUES ({placeholders})"
            with conn.cursor() as cur:
                cur.execute(sql, vals)
    else:
        t = sch["restaurants_table"]
        latc, lngc = sch["lat_col"], sch["lng_col"]
        addr_c, pid_c, src_c = sch["addr_store_col"], sch["place_id_col"], sch["source_col"]
        sets = [f"{latc}=%s", f"{lngc}=%s"]
        vals = [lat, lng]
        if addr_c: sets.append(f"{addr_c}=%s"); vals.append(addr)
        if pid_c: sets.append(f"{pid_c}=%s"); vals.append(place_id)
        if src_c: sets.append(f"{src_c}=%s"); vals.append(provider)
        sql = f"UPDATE {t} SET {', '.join(sets)} WHERE {sch['res_pk']}=%s"
        vals.append(res_id)
        with conn.cursor() as cur:
            cur.execute(sql, vals)

def build_address(name: Optional[str], city: Optional[str], addr: Optional[str], country_hint: Optional[str], loc_name: Optional[str]=None) -> str:
    # Prefer finer-grained fields first
    parts = [p for p in [loc_name, addr, name, city, country_hint] if p and str(p).strip()]
    return ", ".join(parts) if parts else ""

def main():
    ap = argparse.ArgumentParser("Geocode restaurants and store coordinates")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--offset", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--country", default=os.getenv("GEO_COUNTRY_HINT", "Thailand"))
    ap.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    args = ap.parse_args()

    logging.basicConfig(level=args.log_level, format="%(levelname)s %(message)s")

    gm_key = os.getenv("GOOGLE_MAPS_API_KEY")
    ua = os.getenv("NOMINATIM_UA", "DishDiveGeocoder/1.0 (+contact)")
    cache = load_cache()

    conn = pg_connect()
    try:
        sch = pick_schema(conn)
        LOG.info(
            "Schema mode=%s, tables=%s",
            sch["mode"], sch["restaurants_table"] + ("" if sch["mode"]=="inline" else f", {sch['loc_table']}")
        )
        # Clarify which columns will be used to build the address string
        LOG.info(
            "Using columns: name=%s city=%s address=%s (country hint=%s)",
            sch.get("res_name_col"), sch.get("res_city_col"), sch.get("res_addr_col"), args.country,
        )
        if not any([sch.get("res_name_col"), sch.get("res_city_col"), sch.get("res_addr_col")]):
            LOG.warning(
                "No name/city/address columns detected on '%s'. Geocoding will use only the country hint '%s'.\n"
                "Set env overrides RESTAURANTS_NAME_COL / RESTAURANTS_CITY_COL / RESTAURANTS_ADDR_COL to your actual column names.",
                sch["restaurants_table"], args.country,
            )
        rows = select_missing(conn, sch, args.limit, args.offset)
        LOG.info("Found %d restaurants to geocode", len(rows))

        processed = 0
        # Rows differ by mode: when separate, each row corresponds to a location (may have rl_id None)
        for row in rows:
            if sch["mode"] == "separate":
                rl_id, res_id, res_name, loc_name, loc_addr, res_addr, city = row
            else:
                rl_id, res_id, res_name, loc_name, loc_addr, res_addr, city = row

            # Construct best-possible address string
            q = build_address(res_name, city, loc_addr or res_addr, args.country, loc_name)
            if not q:
                LOG.warning("Skipping %s (no addressable fields)", res_id)
                continue

            g = geocode(q, cache, gm_key, ua)
            # Respect OSM rate limits more strictly when falling back
            time.sleep(max(DEFAULT_BATCH_SLEEP, 1.0 if not gm_key else DEFAULT_BATCH_SLEEP))

            if not g:
                LOG.warning("No geocode result for: %s (%s)", res_id, q)
                continue

            LOG.info("Geocoded res=%s rl=%s -> (%.6f, %.6f) %s [%s]", res_id, rl_id, g["lat"], g["lng"], g.get("formatted_address"), g.get("provider"))
            if not args.dry_run:
                upsert_location(conn, sch, rl_id, res_id, g["lat"], g["lng"], g.get("formatted_address"), g.get("place_id"), g.get("provider","?"), inferred_loc_name=loc_name or res_name)
                processed += 1
                if processed % 50 == 0:
                    conn.commit()
        if not args.dry_run:
            conn.commit()
        save_cache(cache)
        LOG.info("Done. Updated %d rows.", processed)
    finally:
        conn.close()

if __name__ == "__main__":
    main()