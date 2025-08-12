-- Create a table with a variety of PostgreSQL data types
-- Requires pgcrypto for gen_random_uuid() (enabled in 01_extensions.sql)

CREATE TABLE IF NOT EXISTS public.gizmos (
    gizmo_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name varchar(120) NOT NULL,
    description text,
    price numeric(10, 2),
    quantity smallint,
    stock bigint,
    active boolean DEFAULT true,
    rating double precision,
    tags text [],
    metadata jsonb,
    serial_bytes bytea,
    launch_date date,
    reminder_time time without time zone,
    duration interval,
    ip_address inet,
    website_url text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

