import asyncio
from pathlib import Path
import random
import uuid
from ncatbot.core import GroupMessage, BotAPI
from sqlmodel import Session
from qq_bot.conn.sql.crud.user_crud import (
    insert_users,
    select_user_by_ids,
    update_users,
)
from qq_bot.core.llm.voice import voice_query
from qq_bot.core.robot.base import AgentBase
from qq_bot.utils.decorator import sql_session
from qq_bot.utils.models import GroupMessageRecord, QUser
from qq_bot.utils.util_text import (
    auto_split_sentence,
    language_classifity,
    typing_time_calculate,
)
from qq_bot.conn.sql.crud.group_message_crud import (
    insert_group_message,
    insert_group_messages,
)

from qq_bot.core import llm_registrar
from qq_bot.utils.config import settings
from qq_bot.utils.logger import logger
from qq_bot.core.llm.llms.chatter import LLMChatter


@sql_session
def update_group_member(
    users: list[QUser], db: Session | None = None
) -> tuple[list, list]:
    updated_users: list[str] = []
    inserted_users: list[str] = []

    try:
        # 更新已有数据
        existed_users = select_user_by_ids(db=db, ids=[u.id for u in users])
        update_users(db=db, users=existed_users, updated_users=users)
        updated_users = [u.nikename for u in existed_users]
        logger.info(f"更新群组用户[{len(existed_users)}]条: {updated_users}")
    except Exception as err:
        logger.error(f"更新群组用户时发生错误: {err}")

    try:
        # 插入新数据
        existed_users_id = {int(u.id) for u in existed_users}  # 使用 set 来加速查找
        new_users: list[QUser] = [u for u in users if int(u.id) not in existed_users_id]
        insert_users(db=db, users=new_users)
        inserted_users = [u.nikename for u in new_users]
        logger.info(f"新增群组用户[{len(new_users)}条]: {inserted_users}")
    except Exception as err:
        logger.error(f"新增群组用户时发生错误: {err}")

    return updated_users, inserted_users


async def send_message(
    api: BotAPI, group_id: int, text: str, voice: bool = True, **kwargs
) -> GroupMessageRecord | None:
    if voice:
        file = Path("cache/tts") / f"voice_{uuid.uuid4().hex}.mp3"
        await voice_query(file=file, text=text)
        result: dict = await api.post_group_file(group_id=group_id, record=str(file))
    else:
        result = await api.post_group_msg(group_id=group_id, text=text, **kwargs)

    if result.get("status") != "ok" or not result.get("data"):
        return None

    msg_id = result["data"].get("message_id", -1)
    reply_data = await api.get_msg(msg_id)

    if reply_data.get("status") != "ok" or not reply_data.get("data"):
        return None

    if voice:
        reply_data["data"]["raw_message"] = text

    return await GroupMessageRecord.from_group_message(
        GroupMessage(reply_data["data"]), True
    )


async def group_chat(
    api: BotAPI,
    message: GroupMessageRecord,
    split: bool = True,
    voice: bool = True,
) -> bool:
    group_id = message.group_id
    split = False if voice else split
    
    llm: LLMChatter = llm_registrar.get(settings.CHATTER_LLM_CONFIG_NAME)
    response: str | None = await llm.run(message)
    if not response:
        return False
    
    messages: list[GroupMessageRecord] = []
    language = language_classifity(response)
    responses: list[str] = (
        [response] if not split else
        auto_split_sentence(response, language, strip_punct=True)
    )
    for text in responses:
        # 模拟打字停顿
        if not voice:
            await asyncio.sleep(typing_time_calculate(text, language))
        # 发送消息
        message = await send_message(api, group_id, text, voice=voice)
        if message:
            messages.append(message)
    
    # 更新memory & 数据库
    llm.update_memory(messages, from_user=False)

    return True
