import uuid
from sqlmodel import Session, select
from typing import Literal
from qq_bot.utils.models import GroupMessageRecord
from qq_bot.conn.sql.models import GroupMessageV1
from qq_bot.utils.util_text import trans_str


def insert_group_message(
    db: Session,
    message: GroupMessageRecord,
) -> None:
    new_msg = GroupMessageV1(
        id=message.str_id(),
        group_id=message.str_group_id(),
        sender_id=message.str_sender_id(),
        reply_message_id=message.str_reply_message_id(),
        at_user_id=message.str_at_user_id(),
        message=message.content,
        from_bot=1 if message.from_bot else 0,
        create_time=message.get_datetime(),
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)


def insert_group_messages(
    db: Session,
    messages: list[GroupMessageRecord],
) -> None:
    db.bulk_insert_mappings(
        GroupMessageV1,
        [
            {
                "id": message.str_id(),
                "group_id": message.str_group_id(),
                "sender_id": message.str_sender_id(),
                "reply_message_id": message.str_reply_message_id(),
                "at_user_id": message.str_at_user_id(),
                "message": message.content,
                "from_bot": 1 if message.from_bot else 0,
                "create_time": message.get_datetime(),
            }
            for message in messages
        ],
    )
    db.commit()
