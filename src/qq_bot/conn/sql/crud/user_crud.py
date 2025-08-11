from cachetools.keys import hashkey
from sqlmodel import Session, col, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from cachetools import LRUCache, cached
from qq_bot.conn.sql.models import QUserModel
from qq_bot.utils.models import QUserData

_user_by_name_cache: LRUCache[str, str] = LRUCache(maxsize=1024 * 10)
_user_by_id_cache: LRUCache[str, str] = LRUCache(maxsize=1024 * 10)


@cached(_user_by_name_cache, key=lambda db, id: str(hashkey(id)))  # noqa
def select_user_by_id(db: Session, id: int) -> QUserModel | None:
    result = db.exec(select(QUserModel).where(QUserModel.id == id)).first()
    return result


def select_user_by_ids(db: Session, ids: list[int]) -> list[QUserModel]:
    result = db.exec(select(QUserModel).where(col(QUserModel.id).in_(ids))).all()
    return list(result)


@cached(_user_by_id_cache, key=lambda db, name: str(hashkey(name)))  # noqa
def select_user_by_name(db: Session, name: str) -> QUserModel | None:
    result = db.exec(select(QUserModel).where(QUserModel.nickname == str(name))).first()
    return result


def insert_users(db: Session, users: list[QUserData] | QUserData) -> None:
    data: list[QUserData] = users if isinstance(users, list) else [users]
    db.bulk_insert_mappings(QUserModel, [user.model_dump() for user in data])
    db.commit()


def update_users(db: Session, users: list[QUserModel], updated_users: list[QUserData]) -> None:
    id_users_mapping = {u.id: u for u in updated_users}

    for user in users:
        q_user = id_users_mapping[user.id]
        for field, value in q_user.model_dump().items():
            setattr(user, field, value)

        _user_by_name_cache.pop(str(hashkey(q_user.nickname)), None)
        _user_by_id_cache.pop(str(hashkey(q_user.id)), None)

    db.add_all(users)
    db.commit()
