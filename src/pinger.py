import os
import sys
import time
import logging
import yaml
import psycopg2

# ------------------------------------------------------------------
# 1. Load trusted connection settings from the config file
# ------------------------------------------------------------------
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")

with open(CONFIG_PATH, "r") as f:
    config_from_file = yaml.safe_load(f)

# Whitelist of allowed keys (security: user/env cannot inject extra options)
ALLOWED_KEYS = {"host", "port", "database", "sslmode", "connect_timeout"}
safe_cfg = {k: v for k, v in config_from_file.items() if k in ALLOWED_KEYS}

# ------------------------------------------------------------------
# 2. Read credentials and interval from ENVIRONMENT VARIABLES
# ------------------------------------------------------------------
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "apppass123")

# Optional override for the host (needed inside docker-compose network)
DB_HOST = os.environ.get("DB_HOST", safe_cfg["host"])

# Interval between checks, default 300 seconds (5 minutes)
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "300"))

# Optional log file path (empty = no file logging)
LOG_FILE = os.environ.get("LOG_FILE", "").strip()

# ------------------------------------------------------------------
# 3. Configure logging: stdout + optional file
# ------------------------------------------------------------------
handlers = [logging.StreamHandler(sys.stdout)]
if LOG_FILE:
    handlers.append(logging.FileHandler(LOG_FILE))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=handlers,
)

log = logging.getLogger("pinger")

# ------------------------------------------------------------------
# 4. Single check: connect, run SELECT VERSION(), classify the result
# ------------------------------------------------------------------
def check_once() -> None:
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=safe_cfg["port"],
            dbname=safe_cfg["database"],
            sslmode=safe_cfg.get("sslmode", "prefer"),
            connect_timeout=safe_cfg.get("connect_timeout", 5),
            user=DB_USER,
            password=DB_PASSWORD,
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION();")
            row = cursor.fetchone()
        connection.close()

        version = row[0] if row else None

        # Successful connection, but non-typical answer → stdout
        if not version or "PostgreSQL" not in str(version):
            log.warning("Connected, but unexpected version response: %r", version)
        else:
            log.info("OK: %s", version)

    except Exception as exc:
        # Any connection / query failure → stderr
        log.error("FAIL: %s: %s", type(exc).__name__, exc)

# ------------------------------------------------------------------
# 5. Main loop: never crash, always retry after the interval
# ------------------------------------------------------------------
def main() -> None:
    log.info("Pinger started. Interval = %s seconds", POLL_INTERVAL_SECONDS)
    while True:
        check_once()
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()