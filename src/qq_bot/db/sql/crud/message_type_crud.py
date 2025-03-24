from cachetools.keys import hashkey
from cachetools import LRUCache, cached
from sqlmodel import Session, select
from qq_bot.db.sql.models import MessageType
from qq_bot.common.logging import logger
from qq_bot.common.config import settings


_msg_type_cache: LRUCache[str, str] = LRUCache(maxsize=1024 * 10)


@cached(_msg_type_cache, key=lambda db, name: str(hashkey(name)))  # noqa
def get_message_type_id_by_name(db: Session, name: str) -> str | None:
    result = db.exec(select(MessageType.id).where(MessageType.name == name)).first()
    return str(result) if result else None


def get_all_message_type(db: Session) -> list[MessageType]:
    result = db.exec(select(MessageType)).all()
    return list(result)


def insert_message_types(db: Session, names: list[str]) -> None:
    if len(names) > 0:
        msg_types = [MessageType(name=name) for name in names]
        db.add_all(msg_types)
        db.commit()
        for msg_type in msg_types:
            db.refresh(msg_type)


def insert_default_msg_type(db: Session):
    default_msg_types = list(settings.DB_GROUP_TYPE_MAPPING.values())
    existed_msg_types = [t.name for t in get_all_message_type(db=db)]
    new_msg_types = [dt for dt in default_msg_types if dt not in existed_msg_types]
    logger.info(f"Existed message type: {existed_msg_types}. New insertion required: {new_msg_types}")
    insert_message_types(db=db, names=new_msg_types)
