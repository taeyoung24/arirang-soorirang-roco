import subprocess
import time

from sqlalchemy import inspect

import db_models  # noqa: F401
from database import Base, engine


BASE_REVISION = "42116df0ca1f"

BASE_TABLES = {
    "categories",
    "learning_sets",
    "words",
    "meanings",
    "sentences",
    "quizzes",
    "quiz_choices",
}

POST_BASE_ADDITIONS = {
    ("sentences", "tts_url"),
    ("quizzes", "sentence_id"),
    ("quizzes", "tts_url"),
    ("recent_learning_records", "*"),
}


def run_alembic(*args):
    subprocess.run(["alembic", *args], check=True)


def wait_for_database():
    while True:
        try:
            with engine.connect() as connection:
                connection.close()
            return
        except Exception:
            time.sleep(2)


def get_schema_state():
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    columns_by_table = {
        table_name: {column["name"] for column in inspector.get_columns(table_name)}
        for table_name in table_names
    }
    return table_names, columns_by_table


def get_missing_model_columns(table_names, columns_by_table):
    missing = set()
    for table_name, table in Base.metadata.tables.items():
        if table_name not in table_names:
            missing.add((table_name, "*"))
            continue

        actual_columns = columns_by_table.get(table_name, set())
        for column_name in table.columns.keys():
            if column_name not in actual_columns:
                missing.add((table_name, column_name))

    return missing


def stamp_legacy_database_if_needed():
    table_names, columns_by_table = get_schema_state()

    if "alembic_version" in table_names:
        return

    managed_tables = set(Base.metadata.tables.keys())
    if not table_names.intersection(managed_tables):
        return

    missing = get_missing_model_columns(table_names, columns_by_table)
    if not missing:
        run_alembic("stamp", "head")
        return

    if BASE_TABLES.issubset(table_names) and missing.issubset(POST_BASE_ADDITIONS):
        run_alembic("stamp", BASE_REVISION)
        return

    missing_text = ", ".join(
        f"{table}.{column}" if column != "*" else table for table, column in sorted(missing)
    )
    raise RuntimeError(
        "Unversioned database schema does not match a known Alembic baseline. "
        f"Missing objects: {missing_text}"
    )


def main():
    wait_for_database()
    stamp_legacy_database_if_needed()
    run_alembic("upgrade", "head")


if __name__ == "__main__":
    main()
