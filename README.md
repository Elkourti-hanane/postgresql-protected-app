# PostgreSQL Protected App — Labs 1, 2, 3

Three labs from the **Development of Protected Software Systems** module,
all sharing the same repository, config-file, whitelist, and Docker patterns.

- **Lab 1** — Interactive app that connects to PostgreSQL and runs `SELECT VERSION();`
- **Lab 2** — Long-running pinger / heartbeat service
- **Lab 3** — Interactive CRUD app over a small "online shop" schema

---

## Repository layout

    .
    ├── config/
    │   └── config.yaml            # trusted connection settings (no credentials)
    ├── docker/
    │   ├── Dockerfile             # image for Lab 2 (pinger)
    │   └── Dockerfile.crud        # image for Lab 3 (CRUD app)
    ├── sql/
    │   ├── schema.sql             # Lab 3 schema (4 related tables)
    │   └── seed.sql               # Lab 3 demo data
    ├── src/
    │   ├── app.py                 # Lab 1
    │   ├── pinger.py              # Lab 2
    │   └── crud_app.py            # Lab 3
    ├── docker-compose.yml         # all services: postgres (Lab 2), pinger, postgres-task3, crud
    ├── postgresql.conf            # Postgres server config (SCRAM-SHA-256)
    ├── requirements.txt
    ├── .env.example               # env template for Lab 2
    ├── .env.crud.example          # env template for Lab 3
    ├── .gitignore
    └── README.md

---

## Lab 1 — Protected PostgreSQL connection

**File:** `src/app.py`

- Reads trusted connection settings from `config/config.yaml`
- Applies a **whitelist** to the config keys (`host`, `port`, `database`, `sslmode`, `connect_timeout`)
- Asks the user for **login and password only** (interactive prompt, password via `getpass`)
- Passes credentials as **keyword arguments** to `psycopg2.connect`, so user input can never become a connection option
- Runs `SELECT VERSION();` and prints the result

**Run**

    python src/app.py

---

## Lab 2 — Pinger / heartbeat service

**File:** `src/pinger.py`

- Runs forever; every `POLL_INTERVAL_SECONDS` seconds it connects to PostgreSQL, runs `SELECT VERSION();`, and logs the result
- **stdout** for successful checks and unexpected-but-not-error responses
- **stderr** for connection failures and exceptions
- Never crashes: everything is wrapped in `try/except`, so a network problem only skips one cycle
- Credentials, interval, and optional log file path come from **environment variables**:
  - `DB_USER`, `DB_PASSWORD`
  - `POLL_INTERVAL_SECONDS` (default 300 = 5 minutes; set to 5 for the demo)
  - `LOG_FILE` (optional path to duplicate logs)

**Docker**

- Image built from `docker/Dockerfile`, tagged `pg-pinger:1.0`
- Wired to Postgres via `docker-compose.yml` and `.env.example`

**Run (inside Docker)**

    docker compose up -d postgres
    docker compose up pinger

---

## Lab 3 — Interactive CRUD app

**Files:** `sql/schema.sql`, `sql/seed.sql`, `src/crud_app.py`, `docker/Dockerfile.crud`

**Database — Online Shop**

Four related tables:

- `categories` (id, name)
- `products` (id, name, category_id → categories, price, stock)
- `customers` (id, full_name, email, city)
- `orders` (id, customer_id → customers, product_id → products, quantity, total, order_date)

**Application features**

1. List all rows of a table
2. Filter by one column (user picks the column and value)
3. Filter by multiple columns (AND)
4. Update one row by id, changing any columns except `id`
5. Update many rows — set one column to a common value for a filtered group
6. Insert one row
7. Insert one row into two related tables (`RETURNING id` from the parent, then used as the foreign key in the child, inside one transaction)

**Security**

- **Whitelist** of allowed tables (`ALLOWED_TABLES`) and per-table columns
- **Whitelist** of updatable columns (`UPDATABLE_COLUMNS`) — `id` is never updatable or insertable
- Column and table names are validated **before** any SQL is built; `f`-strings therefore only ever contain pre-approved identifiers
- **Values** are passed as parameter placeholders (`%s`) so `psycopg2` escapes them — no string concatenation anywhere
- Insert into two related tables runs inside a single transaction with `rollback` on failure
- Database user `shopuser` is not a superuser — it only has `CONNECT` on the database and `USAGE` on the public schema

**Docker**

- Image built from `docker/Dockerfile.crud`, tagged `pg-crud:1.0`
- Runs interactively (`stdin_open: true`, `tty: true`) in the same network as `postgres-task3`

**Run (inside Docker)**

    docker compose up -d postgres-task3
    docker compose run --rm crud

---

## Common security patterns used across all three labs

- Trusted settings come from a **config file**; secrets come from the environment or the user, never hardcoded
- **Whitelist** identifiers (config keys, table names, column names) so they can never carry injected SQL
- Pass **values** as parameterized placeholders (`%s`), never by concatenation
- **Least privilege** for the application database user
- **stdout / stderr** discipline — normal output and errors are separated
- **Docker** for reproducible environments and process isolation
- **git** for versioned, reviewable source code