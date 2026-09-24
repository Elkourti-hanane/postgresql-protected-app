# PostgreSQL Protected Connection App

A small application that connects to PostgreSQL 18 running in Docker.
It reads trusted connection settings from a config file and asks the user
only for credentials, without allowing the user to inject connection options.

## Security design

- Connection parameters (`host`, `port`, `database`, `sslmode`) come **only**
  from `config/config.yaml`, filtered through a whitelist.
- The user provides **only** `login` and `password`.
- Credentials are passed as separate keyword arguments to `psycopg2.connect`,
  so they cannot become connection options.

## Project layout

    src/app.py            – application
    config/config.yaml    – trusted connection settings
    docker/Dockerfile     – container image for the app
    docker-compose.yml    – runs Postgres + the app
    postgresql.conf       – Postgres server config
    requirements.txt      – Python dependencies

## How to run

    docker compose up -d postgres

    # then, on the host (or inside the app container):
    pip install -r requirements.txt
    python src/app.py

## Demo

Login: `appuser`
Password: `apppass123`
Output: the PostgreSQL version (from `SELECT VERSION();`).