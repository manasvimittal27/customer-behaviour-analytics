"""Load the cleaned table into PostgreSQL as ``customer``.

    python -m src.load_to_postgres

Connection settings come from environment variables, so no password is ever
written in code: PGHOST (default localhost), PGPORT (5432), PGUSER (postgres),
PGDATABASE (customer_behaviour) and PGPASSWORD. If PGPASSWORD is not set, the
script asks for it without echoing it.
"""
from __future__ import annotations

import os
from getpass import getpass

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from src.cleaning import clean, load_raw


def make_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD") or getpass("Postgres password: "),
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", "5432")),
        database=os.environ.get("PGDATABASE", "customer_behaviour"),
    )
    return create_engine(url)


def main() -> None:
    df = clean(load_raw())
    engine = make_engine()
    df.to_sql("customer", engine, if_exists="replace", index=False)
    with engine.connect() as conn:
        loaded = conn.execute(text("SELECT COUNT(*) FROM customer")).scalar_one()
    assert loaded == len(df), f"expected {len(df)} rows, found {loaded}"
    print(f"Loaded {loaded:,} rows into table 'customer'.")


if __name__ == "__main__":
    main()
