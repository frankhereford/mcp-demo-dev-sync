## Test MCP Postgres Pro

This project runs a PostgreSQL 17 instance with useful extensions, plus a Python-based data loader for generating fake data into a `gizmos` table.

### What's included

- **PostgreSQL 17** with extensions: `pg_stat_statements`, `hypopg`, `pgcrypto`
- **Initialization SQL** to create the `gizmos` table and triggers
- **Python loader** (`gizmo-loader` service) to insert fake data with a configurable row count

### Prerequisites

- Docker and Docker Compose

### Environment variables

The compose file includes sane defaults. You can override:

- `POSTGRES_USER` (default: `postgres`)
- `POSTGRES_PASSWORD` (default: `postgres`)
- `POSTGRES_DB` (default: `frank`)
- `HOST_PORT` (default: `5432`)

The loader automatically uses these variables via `PG*`/`POSTGRES_*` equivalents to connect.

### Start services

```bash
docker compose up -d postgres
```

Wait for the database to become healthy.

### Create and verify schema

The `initdb` scripts create extensions and the `gizmos` table automatically on first run. To inspect:

```bash
docker compose run --rm psql -c "\d+ public.gizmos"
```

### Load fake data

Run the loader inside a Python image via Compose. Pass the number of rows to insert as an argument.

Usage:

```bash
docker compose run --rm gizmo-loader 5000
```

This will insert 5,000 rows into `public.gizmos`.

### Loader details

The loader image is defined in `loader/Dockerfile` and the program in `loader/load_gizmos.py`.

It supports these environment variables for connection (defaults shown):

- `PGHOST=postgres`
- `PGPORT=5432`
- `PGUSER=postgres`
- `PGPASSWORD=postgres`
- `PGDATABASE=frank`

Override them on the command line, e.g.:

```bash
docker compose run --rm -e PGDATABASE=frank gizmo-loader 1000
```

### Troubleshooting

- Ensure the `postgres` service is healthy before running the loader.
- If you change init SQL and want a fresh database, remove the `postgres_data` volume:

```bash
docker compose down -v
docker compose up -d postgres
```

