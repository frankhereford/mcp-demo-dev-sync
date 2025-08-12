-- Auto-create extensions in the default database on first init
-- pg_stat_statements is in contrib and available when shared_preload_libraries includes it
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- hypopg was compiled into the image; this enables it in the DB
CREATE EXTENSION IF NOT EXISTS hypopg;

-- pgcrypto provides gen_random_uuid() for UUID defaults
CREATE EXTENSION IF NOT EXISTS pgcrypto;
