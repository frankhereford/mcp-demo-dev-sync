import argparse
import os
import random
from datetime import date, datetime, timedelta, time

import psycopg
from psycopg.types.json import Json
from faker import Faker


# Fixed reference data so joins have predictable values
AVAILABLE_COLORS: list[tuple[str, str]] = [
    ("red", "#FF0000"),
    ("green", "#008000"),
    ("blue", "#0000FF"),
    ("yellow", "#FFFF00"),
    ("black", "#000000"),
    ("white", "#FFFFFF"),
    ("purple", "#800080"),
    ("orange", "#FFA500"),
    ("pink", "#FFC0CB"),
    ("brown", "#A52A2A"),
]

CATEGORY_NAMES: list[str] = [
    "Home",
    "Outdoor",
    "Electronics",
    "Toys",
    "Kitchen",
    "Office",
]


def get_connection_dsn() -> str:
    user = os.getenv("PGUSER", os.getenv("POSTGRES_USER", "postgres"))
    password = os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres"))
    host = os.getenv("PGHOST", "postgres")
    port = int(os.getenv("PGPORT", "5432"))
    dbname = os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "frank"))
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def seed_reference_data(cur: psycopg.Cursor) -> None:
    cur.executemany(
        """
        INSERT INTO public.colors (color_name, hex)
        VALUES (%(color_name)s, %(hex)s)
        ON CONFLICT (color_name) DO NOTHING
        """,
        [{"color_name": name, "hex": hex_code} for name, hex_code in AVAILABLE_COLORS],
    )

    cur.executemany(
        """
        INSERT INTO public.categories (category_name, description)
        VALUES (%(name)s, %(description)s)
        ON CONFLICT (category_name) DO NOTHING
        """,
        [
            {
                "name": name,
                "description": f"Category for {name.lower()} products",
            }
            for name in CATEGORY_NAMES
        ],
    )


def generate_gizmo(fake: Faker, color_names: list[str]) -> dict:
    # Generate diverse fake data respecting the schema types
    launch_day = fake.date_between(start_date="-2y", end_date="+1y")
    reminder_time = time(
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
    )
    duration_seconds = random.randint(60, 60 * 60 * 24)
    duration = timedelta(seconds=duration_seconds)

    # Sometimes include None for optional fields
    maybe = lambda val: val if random.random() > 0.1 else None

    return {
        "name": fake.unique.catch_phrase()[:120],
        "description": maybe(fake.paragraph(nb_sentences=3)),
        "price": maybe(round(random.uniform(1, 9999), 2)),
        "quantity": maybe(random.randint(0, 32767)),
        "stock": maybe(random.randint(0, 1_000_000_000)),
        "active": random.random() > 0.2,
        "rating": maybe(round(random.uniform(0, 5), 3)),
        "tags": maybe([fake.word() for _ in range(random.randint(0, 5))]) or [],
        "metadata": Json(
            maybe(
                {
                    "color": random.choice(color_names),
                    "size": random.choice(["S", "M", "L", "XL"]),
                    "warranty_years": random.randint(0, 5),
                }
            )
            or {}
        ),
        "serial_bytes": maybe(os.urandom(random.randint(0, 16))),
        "launch_date": maybe(launch_day),
        "reminder_time": maybe(reminder_time),
        "duration": maybe(duration),
        "ip_address": maybe(
            fake.ipv4_public() if random.random() > 0.5 else fake.ipv6()
        ),
        "website_url": maybe(fake.url()),
    }


def insert_rows(dsn: str, num_rows: int) -> None:
    fake = Faker()
    with psycopg.connect(dsn, autocommit=False) as conn:
        with conn.cursor() as cur:
            # Ensure reference tables exist and are populated
            seed_reference_data(cur)

            color_names = [name for name, _ in AVAILABLE_COLORS]

            insert_gizmo_sql = """
                INSERT INTO public.gizmos (
                    name, description, price, quantity, stock, active, rating, tags,
                    metadata, serial_bytes, launch_date, reminder_time, duration,
                    ip_address, website_url
                )
                VALUES (
                    %(name)s, %(description)s, %(price)s, %(quantity)s, %(stock)s, %(active)s, %(rating)s, %(tags)s,
                    %(metadata)s, %(serial_bytes)s, %(launch_date)s, %(reminder_time)s, %(duration)s,
                    %(ip_address)s, %(website_url)s
                )
                RETURNING gizmo_id
            """

            insert_review_sql = """
                INSERT INTO public.gizmo_reviews (
                    gizmo_id, reviewer_name, rating, comment
                ) VALUES (%(gizmo_id)s, %(reviewer_name)s, %(rating)s, %(comment)s)
            """

            insert_gizmo_category_sql = """
                INSERT INTO public.gizmo_categories (gizmo_id, category_id)
                SELECT %(gizmo_id)s, c.category_id
                FROM public.categories c
                WHERE c.category_name = %(category_name)s
                ON CONFLICT (gizmo_id, category_id) DO NOTHING
            """

            commit_every = 1000
            for i in range(num_rows):
                gizmo_data = generate_gizmo(fake, color_names)
                cur.execute(insert_gizmo_sql, gizmo_data)
                gizmo_id = cur.fetchone()[0]

                # Add 0-3 reviews per gizmo
                num_reviews = random.randint(0, 3)
                if num_reviews > 0:
                    reviews = [
                        {
                            "gizmo_id": gizmo_id,
                            "reviewer_name": fake.name(),
                            "rating": random.randint(1, 5),
                            "comment": fake.sentence(nb_words=12),
                        }
                        for _ in range(num_reviews)
                    ]
                    cur.executemany(insert_review_sql, reviews)

                # Link 1-3 categories via intermediate table
                num_cats = random.randint(1, 3)
                chosen_categories = random.sample(CATEGORY_NAMES, k=num_cats)
                cur.executemany(
                    insert_gizmo_category_sql,
                    [
                        {"gizmo_id": gizmo_id, "category_name": cat_name}
                        for cat_name in chosen_categories
                    ],
                )

                if (i + 1) % commit_every == 0:
                    conn.commit()
                    print(f"Inserted {i + 1} / {num_rows}")

            conn.commit()
            print(f"Inserted {num_rows} / {num_rows}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Insert fake gizmos into PostgreSQL")
    parser.add_argument("num_rows", type=int, help="Number of rows to insert")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dsn = get_connection_dsn()
    print(f"Connecting to {dsn}")
    insert_rows(dsn, args.num_rows)
    print("Done")


if __name__ == "__main__":
    main()
