## Demo an MCP - Postgres Pro

Open source repo found here: https://github.com/crystaldba/postgres-mcp

This project runs a PostgreSQL 17 instance with useful extensions, plus a Python-based data loader for generating fake data into a `gizmos` table and related tables for join demos.

### What's included

- **PostgreSQL 17** with extensions: `pg_stat_statements`, `hypopg`, `pgcrypto`
- **Initialization SQL** to create:
  - `public.gizmos` (primary table with many data types)
  - `public.gizmo_reviews` (one-to-many by `gizmo_id`)
  - `public.categories` and `public.gizmo_categories` (many-to-many via intermediate table)
  - `public.colors` (joined via JSON operator against `gizmos.metadata`)
- **Python loader** (`gizmo-loader` service) to insert fake data with a configurable row count, plus related rows

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

The `initdb` scripts create extensions and all tables automatically on first run. To inspect:

```bash
docker compose run --rm psql -c "\d+ public.gizmos"
```

### Load fake data

Run the loader inside a Python image via Compose. Pass the number of rows to insert as an argument.

Usage:

```bash
docker compose run --rm gizmo-loader 5000
```

This will insert 5,000 rows into `public.gizmos` and also:

- Create 0–3 `public.gizmo_reviews` per gizmo (joined by `gizmo_id`)
- Attach 1–3 categories per gizmo via `public.gizmo_categories`
- Seed `public.colors` and set `gizmos.metadata->>'color'` to match one of the seeded color names

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

### Schema overview

- `public.gizmos`:

  - Primary key: `gizmo_id uuid`
  - Has diverse column types (numeric, boolean, arrays, jsonb, inet, etc.)
  - `metadata jsonb` contains keys such as `color`, `size`, `warranty_years`

- `public.gizmo_reviews` (vanilla one-to-many):

  - `gizmo_id` → `gizmos.gizmo_id`
  - Example: join directly by UUID foreign key

- `public.categories` and `public.gizmo_categories` (many-to-many):

  - `gizmo_categories (gizmo_id, category_id)` links each gizmo to one or more categories

- `public.colors` (JSON operator join):
  - Join on `(g.metadata->>'color') = colors.color_name`

Nothing is optimized; this is purposely simple for performance analysis demos.

### Example joins

- Simple one-to-many join by ID (`gizmos` ↔ `gizmo_reviews`):

```sql
SELECT g.gizmo_id,
       g.name,
       r.rating,
       r.comment,
       r.created_at AS review_created_at
FROM public.gizmos AS g
JOIN public.gizmo_reviews AS r
  ON r.gizmo_id = g.gizmo_id
ORDER BY r.created_at DESC
LIMIT 10;
```

- Many-to-many via intermediate table (`gizmos` ↔ `gizmo_categories` ↔ `categories`):

```sql
SELECT g.gizmo_id,
       g.name,
       array_agg(DISTINCT c.category_name ORDER BY c.category_name) AS categories
FROM public.gizmos AS g
JOIN public.gizmo_categories AS gc
  ON gc.gizmo_id = g.gizmo_id
JOIN public.categories AS c
  ON c.category_id = gc.category_id
GROUP BY g.gizmo_id, g.name
ORDER BY g.name
LIMIT 10;
```

- Join using a JSON operator (`gizmos.metadata->>'color'` ↔ `colors.color_name`):

```sql
SELECT g.gizmo_id,
       g.name,
       g.metadata->>'color' AS color,
       c.hex AS color_hex
FROM public.gizmos AS g
LEFT JOIN public.colors AS c
  ON (g.metadata->>'color') = c.color_name
WHERE g.metadata ? 'color'
ORDER BY g.name
LIMIT 10;
```

- Bonus: average rating per gizmo with category context and color (combines all three patterns):

```sql
WITH avg_reviews AS (
  SELECT r.gizmo_id, avg(r.rating)::numeric(10,2) AS avg_rating
  FROM public.gizmo_reviews r
  GROUP BY r.gizmo_id
)
SELECT g.gizmo_id,
       g.name,
       ar.avg_rating,
       array_agg(DISTINCT c.category_name ORDER BY c.category_name) AS categories,
       g.metadata->>'color' AS color,
       col.hex AS color_hex
FROM public.gizmos g
LEFT JOIN avg_reviews ar ON ar.gizmo_id = g.gizmo_id
LEFT JOIN public.gizmo_categories gc ON gc.gizmo_id = g.gizmo_id
LEFT JOIN public.categories c ON c.category_id = gc.category_id
LEFT JOIN public.colors col ON (g.metadata->>'color') = col.color_name
GROUP BY g.gizmo_id, g.name, ar.avg_rating, col.hex
ORDER BY coalesce(ar.avg_rating, 0) DESC NULLS LAST, g.name
LIMIT 20;
```

## Fun questions

- How many records to I have in each table? Disk space? Is this too many?
- what is the most common color of gizmo?

```text
I've got a query and it's slow. can you give me some tips? don't do anything, just let me know what ideas you have

WITH avg_reviews AS (
  SELECT r.gizmo_id, avg(r.rating)::numeric(10,2) AS avg_rating
  FROM public.gizmo_reviews r
  GROUP BY r.gizmo_id
)
SELECT g.gizmo_id,
       g.name,
       ar.avg_rating,
       array_agg(DISTINCT c.category_name ORDER BY c.category_name) AS categories,
       g.metadata->>'color' AS color,
       col.hex AS color_hex
FROM public.gizmos g
LEFT JOIN avg_reviews ar ON ar.gizmo_id = g.gizmo_id
LEFT JOIN public.gizmo_categories gc ON gc.gizmo_id = g.gizmo_id
LEFT JOIN public.categories c ON c.category_id = gc.category_id
LEFT JOIN public.colors col ON (g.metadata->>'color') = col.color_name
GROUP BY g.gizmo_id, g.name, ar.avg_rating, col.hex
ORDER BY coalesce(ar.avg_rating, 0) DESC NULLS LAST, g.name
```

- Are any already there?

- Can you create a SQL view that shows the z-scores of the price of my gizmos, so I can analyze the distribution? Even though this repo has the fixings to build up the database, don't get fooled - i want you to simply add the view to the database. Go ahead and create a new folder called 'views' too and drop the source in there pls. name it up.sql like a migration and make me a down one too. k thx bye

- Look into my data and give me insights about it. What patterns are there?
