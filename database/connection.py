from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "chinook.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


def get_engine() -> Engine:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    return create_engine(
        DATABASE_URL,
        connect_args={"timeout": 10},
    )


if __name__ == "__main__":
    engine = get_engine()

    with engine.connect():
        print("Database connection successful!")
        print(f"Database file: {DATABASE_PATH}")