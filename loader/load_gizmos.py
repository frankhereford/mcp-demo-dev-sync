import argparse
import os
import random
from datetime import date, datetime, timedelta, time

import psycopg
from psycopg.types.json import Json
from faker import Faker


def get_connection_dsn() -> str:
    user = os.getenv("PGUSER", os.getenv("POSTGRES_USER", "postgres"))
    password = os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "postgres"))
    host = os.getenv("PGHOST", "postgres")
    port = int(os.getenv("PGPORT", "5432"))
    dbname = os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "frank"))
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def generate_gizmo(fake: Faker) -> dict:
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
                    "color": fake.safe_color_name(),
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
            insert_sql = """
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
                """

            batch: list[dict] = []
            batch_size = 1000
            for i in range(num_rows):
                batch.append(generate_gizmo(fake))
                if len(batch) >= batch_size:
                    cur.executemany(insert_sql, batch)
                    conn.commit()
                    print(f"Inserted {i + 1} / {num_rows}")
                    batch.clear()

            if batch:
                cur.executemany(insert_sql, batch)
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
