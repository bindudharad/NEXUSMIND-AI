from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.postgres_dsn, pool_pre_ping=True, connect_args={"connect_timeout": 1})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
