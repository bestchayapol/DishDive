import os
import psycopg2
import psycopg2.extras

OUTPUT = os.getenv("REAL_LOCATIONS_OUTPUT", "real_locations.txt")

def pg_connect():
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", ""),
        dbname=os.getenv("PG_DATABASE", "postgres"),
        connect_timeout=10,
    )

SQL = """
SELECT r.res_id, r.res_name, rl.rl_id, rl.location_name, rl.address, rl.latitude, rl.longitude
FROM restaurants r
JOIN restaurant_locations rl ON rl.res_id = r.res_id
WHERE rl.latitude IS NOT NULL AND rl.longitude IS NOT NULL
  AND rl.latitude <> 0 AND rl.longitude <> 0
  AND (rl.address IS NULL OR rl.address <> 'Thailand')
ORDER BY r.res_id, rl.rl_id;
"""

if __name__ == "__main__":
    conn = pg_connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(SQL)
            rows = cur.fetchall()
        with open(OUTPUT, "w", encoding="utf-8") as f:
            for row in rows:
                line = f"{row['res_id']}\t{row['res_name']}\t{row['rl_id']}\t{row['location_name']}\t{row['address']}\t{row['latitude']},{row['longitude']}\n"
                f.write(line)
        print(f"Wrote {len(rows)} rows to {OUTPUT}")
    finally:
        conn.close()
