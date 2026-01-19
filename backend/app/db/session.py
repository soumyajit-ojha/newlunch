from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings
from app.utils.log_config import logger

# Construct the URL
DATABASE_URL = f"postgresql://{settings.DB_USER}:{quote_plus(settings.DB_PASSWORD)}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # How many persistent connections to keep
    max_overflow=10,  # How many extra to open during spikes
    pool_recycle=3600,
    pool_pre_ping=True,  # Checks if RDS connection is alive before using it
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.exception("DB session error: %s", e)
        raise
    finally:
        db.close()
