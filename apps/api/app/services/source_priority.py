from sqlalchemy import inspect, text

from app.db.session import engine

SOURCE_PRIORITIES = {
    "stripe": 1,
    "quickbooks": 2,
    "hubspot": 3,
    "linear": 4,
    "notion": 5,
    "slack": 6,
    "manual_seed": 99,
}

DEFAULT_SOURCE_PRIORITY = 99


def get_source_priority(source_system: str) -> int:
    return SOURCE_PRIORITIES.get(source_system.lower(), DEFAULT_SOURCE_PRIORITY)


def ensure_source_priority_column() -> None:
    inspector = inspect(engine)
    if "knowledge_items" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("knowledge_items")}
    if "source_priority" in columns:
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE knowledge_items "
                "ADD COLUMN source_priority INTEGER NOT NULL DEFAULT 99"
            )
        )
        for source_system, priority in SOURCE_PRIORITIES.items():
            conn.execute(
                text(
                    "UPDATE knowledge_items "
                    "SET source_priority = :priority "
                    "WHERE source_system = :source_system"
                ),
                {"priority": priority, "source_system": source_system},
            )


def ensure_allowed_roles_column() -> None:
    inspector = inspect(engine)
    if "knowledge_items" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("knowledge_items")}
    if "allowed_roles" in columns:
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE knowledge_items "
                "ADD COLUMN allowed_roles VARCHAR[] NOT NULL "
                "DEFAULT ARRAY['founder','admin','member']::VARCHAR[]"
            )
        )


def ensure_timestamp_columns() -> None:
    inspector = inspect(engine)
    if "knowledge_items" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("knowledge_items")}

    with engine.begin() as conn:
        if "created_at" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE knowledge_items "
                    "ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
                )
            )
        if "updated_at" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE knowledge_items "
                    "ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
                )
            )


def ensure_importance_score_column() -> None:
    inspector = inspect(engine)
    if "knowledge_definitions" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("knowledge_definitions")}
    if "importance_score" in columns:
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE knowledge_definitions "
                "ADD COLUMN importance_score INTEGER NOT NULL DEFAULT 5"
            )
        )


def ensure_is_active_column() -> None:
    inspector = inspect(engine)
    if "knowledge_items" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("knowledge_items")}
    if "is_active" in columns:
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE knowledge_items "
                "ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"
            )
        )
