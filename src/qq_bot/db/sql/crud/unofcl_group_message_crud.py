import uuid
from sqlmodel import Session, select
from typing import Literal
from qq_bot.basekit.models import GroupMessageRecord
from qq_bot.db.sql.crud.ofcl_message_type_crud import get_message_type_id_by_name
from qq_bot.db.sql.models import OfficialGroupBotMessage, OfficialGroupChatMessage, OfficialGroupQueryRecordRelation, OfficialMessageType, UnofficialGroupMessageV1


def insert_group_message(
    db: Session, 
    message: GroupMessageRecord,
    is_bot: bool
) -> None:
    new_msg = UnofficialGroupMessageV1(
        id=message.id,
        group_id=message.group_id,
        sender_id=message.sender_id,
        reply_message_id=message.reply_message_id,
        at_user_id=message.at_user_id,
        message=message.content,
        is_bot=1 if is_bot else 0,
        create_time=message.get_datetime(),
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)