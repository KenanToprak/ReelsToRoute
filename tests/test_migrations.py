from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from core.config import settings


def test_alembic_upgrade_downgrade_round_trip(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "alembic roundtrip.db"
    # Include URL-encoded %20 to verify ConfigParser % escaping in alembic/env.py
    db_url = f"sqlite:///{db_path.as_posix().replace(' ', '%20')}"
    monkeypatch.setattr(settings, "DATABASE_URL", db_url)

    repo_root = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(repo_root / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(repo_root / "alembic"))

    # Upgrade from empty DB to head
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(db_url)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert {"users", "routes", "locations"}.issubset(tables)

        route_cols = {col["name"]: col for col in inspector.get_columns("routes")}
        assert "estimated_days" in route_cols
        assert route_cols["estimated_days"]["nullable"] is False

        location_fks = inspector.get_foreign_keys("locations")
        fk_targets = {fk["referred_table"]: fk for fk in location_fks}
        assert "users" in fk_targets
        assert "routes" in fk_targets
    finally:
        engine.dispose()

    # Downgrade all the way back to base
    command.downgrade(alembic_cfg, "base")

    engine = create_engine(db_url)
    try:
        inspector = inspect(engine)
        tables_after_downgrade = set(inspector.get_table_names())
        assert "users" not in tables_after_downgrade
        assert "routes" not in tables_after_downgrade
        assert "locations" not in tables_after_downgrade
    finally:
        engine.dispose()

    # Re-upgrade cleanly to head
    command.upgrade(alembic_cfg, "head")
    engine = create_engine(db_url)
    try:
        inspector = inspect(engine)
        assert {"users", "routes", "locations"}.issubset(set(inspector.get_table_names()))
    finally:
        engine.dispose()
