import time
import json
import psycopg2
import psycopg2.extras as pg_extras
from psycopg2 import pool as pg_pool
from contextlib import contextmanager
from typing import Optional
from .config import Config

class DB:
    def __init__(self, cfg: Config, logger):
        self.cfg = cfg
        self.logger = logger
        self._pool: Optional[pg_pool.SimpleConnectionPool] = None
        self._available: Optional[bool] = None
        self._last_check_ts: Optional[float] = None

    def init_pool(self):
        if self._pool is not None:
            return
        try:
            self._pool = pg_pool.SimpleConnectionPool(
                minconn=self.cfg.pg_pool_min,
                maxconn=self.cfg.pg_pool_max,
                host=self.cfg.pg_host,
                port=self.cfg.pg_port,
                user=self.cfg.pg_user,
                password=self.cfg.pg_password,
                dbname=self.cfg.pg_database,
                connect_timeout=5,
                sslmode=self.cfg.pg_sslmode,
            )
        except Exception as e:
            self.logger.warning("Failed to init PG pool; falling back to direct connections: %s", e)
            self._pool = None

    @contextmanager
    def conn(self):
        self.init_pool()
        if self._pool is not None:
            c = self._pool.getconn()
            try:
                yield c
            finally:
                try:
                    self._pool.putconn(c)
                except Exception:
                    try:
                        c.close()
                    except Exception:
                        pass
        else:
            c = psycopg2.connect(
                host=self.cfg.pg_host,
                port=self.cfg.pg_port,
                user=self.cfg.pg_user,
                password=self.cfg.pg_password,
                dbname=self.cfg.pg_database,
                connect_timeout=5,
                sslmode=self.cfg.pg_sslmode,
            )
            try:
                yield c
            finally:
                try:
                    c.close()
                except Exception:
                    pass

    def writes_enabled(self) -> bool:
        return not self.cfg.pg_write_disabled

    def is_available(self, cooldown_sec: int = 120) -> bool:
        if not self.writes_enabled():
            return False
        now = time.time()
        if self._available is False and self._last_check_ts and (now - self._last_check_ts) < cooldown_sec:
            return False
        try:
            with self.conn() as c:
                pass
            self._available = True
        except Exception as e:
            self._available = False
            self.logger.warning("Postgres unavailable: %s", e)
        self._last_check_ts = now
        return bool(self._available)

    def ensure_table(self):
        if not self.is_available():
            self.logger.warning("Postgres not reachable; skipping table init.")
            return
        ddl = """
        CREATE TABLE IF NOT EXISTS review_extracts (
            rev_ext_id BIGINT PRIMARY KEY,
            source_id BIGINT,
            source_type VARCHAR(64) NOT NULL,
            data_extract TEXT
        );
        """
        with self.conn() as c:
            with c.cursor() as cur:
                cur.execute(ddl)
            c.commit()

    def get_max_rev_ext_id(self) -> int:
        try:
            with self.conn() as c:
                with c.cursor() as cur:
                    cur.execute("SELECT COALESCE(MAX(rev_ext_id), 0) FROM review_extracts")
                    base = cur.fetchone()[0] or 0
            return int(base)
        except Exception:
            return 0

    def upsert_review_extracts(self, results: list, source_type: str = "web") -> int:
        if not self.is_available():
            return 0
        rows = []
        skipped_filtered = 0
        for r in results:
            try:
                if r.get("Status") != "Success":
                    continue
            except AttributeError:
                continue
            rn = r.get("Row Number")
            data_json = r.get("Extracted JSON")
            if rn is None or data_json is None:
                continue
            # Filter out any dish entries where dish contains 'เมนูรวม'
            try:
                arr = json.loads(data_json)
                if isinstance(arr, list):
                    arr = [o for o in arr if not (isinstance(o, dict) and isinstance(o.get("dish"), str) and ("เมนูรวม" in o.get("dish")))]
                else:
                    arr = []
            except Exception:
                arr = []
            if not arr:
                skipped_filtered += 1
                continue
            filtered_json = json.dumps(arr, ensure_ascii=False)
            rows.append((int(rn), source_type, filtered_json))
        if not rows:
            if skipped_filtered:
                self.logger.info("DB upsert skipped %s rows after filter (เมนูรวม)", skipped_filtered)
            return 0
        base = self.get_max_rev_ext_id()
        values_with_ids = [(base + i, sid, s_type, data_json) for i, (sid, s_type, data_json) in enumerate(rows, start=1)]
        with self.conn() as c:
            with c.cursor() as cur:
                pg_extras.execute_values(
                    cur,
                    """
                    INSERT INTO review_extracts (rev_ext_id, source_id, source_type, data_extract)
                    VALUES %s
                    ON CONFLICT (rev_ext_id) DO UPDATE SET
                        source_id = EXCLUDED.source_id,
                        source_type = EXCLUDED.source_type,
                        data_extract = EXCLUDED.data_extract
                    """,
                    values_with_ids,
                    page_size=1000,
                )
            c.commit()
        if skipped_filtered:
            self.logger.info("DB upsert inserted %s rows; skipped %s filtered", len(values_with_ids), skipped_filtered)
        return len(values_with_ids)
