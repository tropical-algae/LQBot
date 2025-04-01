
from cachetools.keys import hashkey
from sqlmodel import Session, select
from cachetools import LRUCache, cached
from qq_bot.conn.sql.models import UserV1
from qq_bot.utils.models import QUser
from qq_bot.utils.util_text import trans_int, trans_str

_user_by_name_cache: LRUCache[str, str] = LRUCache(maxsize=1024 * 10)
_user_by_id_cache: LRUCache[str, str] = LRUCache(maxsize=1024 * 10)


@cached(_user_by_name_cache, key=lambda db, id: str(hashkey(id)))  # noqa
def select_user_by_id(db: Session, id: int) -> UserV1 | None:
    result = db.exec(
        select(UserV1)
        .where(UserV1.id == str(id))
    ).first()
    return result


@cached(_user_by_id_cache, key=lambda db, name: str(hashkey(name)))  # noqa
def select_user_by_name(db: Session, name: str) -> UserV1 | None:
    result = db.exec(
        select(UserV1)
        .where(UserV1.nikename == str(name))
    ).first()
    return result


def insert_user(db: Session, user: QUser, group_id: int | None = None):
    new_user = UserV1(
        id=trans_str(user.id),
        nikename=user.nikename,
        sex=user.sex,
        age=user.age,
        long_nick=user.long_nick
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)


def update_user(db: Session, user: UserV1, **kwargs):
    user = user.model_validate(**kwargs)
    db.add(user)
    db.commit()
    db.refresh(user)
