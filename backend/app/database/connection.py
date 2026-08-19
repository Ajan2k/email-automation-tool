import logging
import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger("app.database")

db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(max_retries: int = 5, delay: float = 2.0) -> None:
    import app.models  # noqa: F401
    from app.database.base import Base
    from sqlalchemy.exc import IntegrityError, ProgrammingError

    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables initialized successfully.")
            break
        except (IntegrityError, ProgrammingError) as exc:
            if "already exists" in str(exc).lower() or "duplicate key" in str(exc).lower():
                logger.info("Database schema elements already exist. Continuing startup.")
                break
            raise exc
        except OperationalError as exc:
            if attempt == max_retries:
                logger.error("Failed to connect to database after %s attempts", max_retries)
                raise exc
            logger.warning(
                "Database connection failed (attempt %s/%s). Retrying in %ss...",
                attempt,
                max_retries,
                delay,
            )
            time.sleep(delay)

