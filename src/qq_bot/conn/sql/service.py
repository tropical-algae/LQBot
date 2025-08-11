
from collections import defaultdict
from sqlmodel import Session

from qq_bot.conn.sql.crud.group_message_crud import insert_group_message, insert_group_messages, select_current_group_messages
from qq_bot.conn.sql.crud.user_crud import select_user_by_id
from qq_bot.utils.decorator import sql_session
from qq_bot.utils.logger import logger
from qq_bot.utils.models import GroupMessageData, QUserData
from qq_bot.conn.sql.crud.group_message_crud import (
    insert_group_message,
    insert_group_messages,
)
from qq_bot.conn.sql.crud.user_crud import (
    insert_users,
    select_user_by_ids,
    update_users,
)


@sql_session
def load_messages(db: Session, count: int) -> dict[str, list[GroupMessageData]]:
    result: dict[str, list[GroupMessageData]] = defaultdict(list)
    group_messages = select_current_group_messages(db=db, count=count)
    for group_id, messages in group_messages.items():
        for message in messages:
            sender = select_user_by_id(db=db, id=message.sender_id)
            receiver = select_user_by_id(db=db, id=message.receiver_id) if message.receiver_id else None
            
            if sender is not None:
                result[group_id].append(
                    GroupMessageData.from_group_message_model(
                        data=message, sender=sender, receiver=receiver
                    )
                )
    return result


@sql_session
def record_messages(
    messages: list[GroupMessageData] | GroupMessageData,
    db: Session | None = None,
) -> None:
    if db is None:
        return

    try:
        abs: str = ""
        if isinstance(messages, list):
            insert_group_messages(db=db, messages=messages)
            abs = ", ".join([f"{i.content[:4]}.." for i in messages])
        elif isinstance(messages, GroupMessageData):
            insert_group_message(db=db, message=messages)
            abs = f"{messages.content[:5]}.."
        else:
            return
        logger.info(f"聊天记录已存储: {abs}")
    except Exception as err:
        logger.error(f"{err}. 聊天记录存储失败: {abs}")


@sql_session
def update_group_member(
    qusers: list[QUserData], db: Session | None = None
) -> tuple[list, list]:
    updated_users: list[str] = []
    inserted_users: list[str] = []
    try:
        # 更新已有数据
        existed_users = select_user_by_ids(db=db, ids=[u.id for u in qusers])
        update_users(db=db, users=existed_users, updated_users=qusers)
        updated_users = [u.nickname for u in existed_users]
        logger.info(f"更新群组用户[{len(existed_users)}]条: {updated_users}")
    except Exception as err:
        logger.error(f"更新群组用户时发生错误: {err}")

    try:
        # 插入新数据
        existed_users_id = {u.id for u in existed_users}  # 使用 set 来加速查找
        new_users: list[QUserData] = [u for u in qusers if u.id not in existed_users_id]
        insert_users(db=db, users=new_users)
        inserted_users = [u.nickname for u in new_users]
        logger.info(f"新增群组用户[{len(new_users)}条]: {inserted_users}")
    except Exception as err:
        logger.error(f"新增群组用户时发生错误: {err}")

    return updated_users, inserted_users