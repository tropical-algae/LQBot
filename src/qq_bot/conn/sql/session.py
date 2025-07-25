from qq_bot.conn.sql.models import *

from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Session, create_engine, select
from qq_bot.utils.logger import logger
from qq_bot.utils.config import settings


local_engine = create_engine(
    url=settings.SQL_DATABASE_URI, pool_pre_ping=True, echo=settings.DEBUG
)
LocalSession = sessionmaker(
    autocommit=False, autoflush=False, bind=local_engine, class_=Session
)

logger.info(f"[init] Checking database consistency...")
SQLModel.metadata.create_all(local_engine)

