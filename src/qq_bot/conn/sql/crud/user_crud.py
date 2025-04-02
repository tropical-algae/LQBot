from cachetools.keys import hashkey
from sqlmodel import Session, col, select
from cachetools import LRUCache, cached
from qq_bot.conn.sql.models import UserV1
from qq_bot.utils.models import QUser
from qq_bot.utils.util_text import trans_int, trans_str

_user_by_name_cache: LRUCache[str, str] = LRUCache(maxsize=1024 * 10)
_user_by_id_cache: LRUCache[str, str] = LRUCache(maxsize=1024 * 10)


@cached(_user_by_name_cache, key=lambda db, id: str(hashkey(id)))  # noqa
def select_user_by_id(db: Session, id: int) -> UserV1 | None:
    result = db.exec(select(UserV1).where(UserV1.id == str(id))).first()
    return result


def select_user_by_ids(db: Session, ids: list[int]) -> list[UserV1]:
    result = db.exec(select(UserV1).where(col(UserV1.id).in_(ids))).all()
    return list(result)


@cached(_user_by_id_cache, key=lambda db, name: str(hashkey(name)))  # noqa
def select_user_by_name(db: Session, name: str) -> UserV1 | None:
    result = db.exec(select(UserV1).where(UserV1.nikename == str(name))).first()
    return result


def insert_users(db: Session, users: list[QUser] | QUser) -> None:
    data: list[QUser] = users if isinstance(users, list) else [users]

    db.bulk_insert_mappings(UserV1, [user.to_dict() for user in data])
    db.commit()


def update_users(db: Session, users: list[UserV1], updated_users: list[QUser]) -> None:
    id_users_mapping = {int(u.id): u for u in updated_users}

    for user in users:
        q_user = id_users_mapping[int(user.id)]
        for field, value in q_user.to_dict().items():
            setattr(user, field, value)

        # 清除缓存
        _user_by_name_cache.pop(str(hashkey(q_user.nikename)), None)
        _user_by_id_cache.pop(str(hashkey(q_user.id)), None)

    # 批量提交更新的用户
    db.add_all(users)
    db.commit()
