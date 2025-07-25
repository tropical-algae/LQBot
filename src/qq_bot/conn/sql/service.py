
from sqlmodel import Session


from qq_bot.conn.sql.crud.group_message_crud import insert_group_message, insert_group_messages
from qq_bot.utils.decorator import sql_session
from qq_bot.utils.logger import logger
from qq_bot.utils.models import GroupMessageRecord


@sql_session
def record_messages(
    messages: list[GroupMessageRecord] | GroupMessageRecord,
    db: Session | None = None,
) -> None:
    if db is None:
        return

    try:
        abs: str = ""
        if isinstance(messages, list):
            insert_group_messages(db=db, messages=messages)
            abs = ", ".join([f"{i.content[:4]}.." for i in messages])
        elif isinstance(messages, GroupMessageRecord):
            insert_group_message(db=db, message=messages)
            abs = f"{messages.content[:5]}.."
        else:
            return
        logger.info(f"聊天记录已存储: {abs}")
    except Exception as err:
        logger.error(f"{err}. 聊天记录存储失败: {abs}")