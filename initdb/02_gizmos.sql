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

-- Simple one-to-many table joined by gizmo_id
CREATE TABLE IF NOT EXISTS public.gizmo_reviews (
    review_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    gizmo_id uuid NOT NULL
    REFERENCES public.gizmos (gizmo_id)
    ON DELETE CASCADE,
    reviewer_name text,
    rating smallint CHECK (rating BETWEEN 1 AND 5),
    comment text,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Many-to-many via intermediate table
CREATE TABLE IF NOT EXISTS public.categories (
    category_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    category_name text NOT NULL UNIQUE,
    description text
);

CREATE TABLE IF NOT EXISTS public.gizmo_categories (
    gizmo_id uuid NOT NULL
    REFERENCES public.gizmos (gizmo_id)
    ON DELETE CASCADE,
    category_id uuid NOT NULL
    REFERENCES public.categories (category_id)
    ON DELETE CASCADE,
    added_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (gizmo_id, category_id)
);

-- Table intended to be joined via a JSON operator against gizmos.metadata
-- Join example: ... ON (g.metadata->>'color') = c.color_name
CREATE TABLE IF NOT EXISTS public.colors (
    color_name text PRIMARY KEY,
    hex text
);

-- end of schema
