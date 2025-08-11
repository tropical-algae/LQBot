import asyncio
from pathlib import Path
import random
import uuid
from ncatbot.core import GroupMessage, BotAPI

from qq_bot.conn.sql.service import update_group_member
from qq_bot.core.llm.voice import voice_query
from qq_bot.utils.models import GroupMessageData, QUserData
from qq_bot.utils.util import (
    auto_split_sentence,
    language_classifity,
    typing_time_calculate,
)

from qq_bot.core import llm_registrar
from qq_bot.utils.config import settings
from qq_bot.utils.logger import logger
from qq_bot.core.llm.llms.chatter import LLMChatter

TTS_ROOT = Path(settings.TTS_CACHE_ROOT)
TTS_ROOT.mkdir(parents=True, exist_ok=True)


async def init_agent(
    api: BotAPI
) -> None:
    groups: dict = await api.get_group_list()
    if groups.get("status") == "ok":
        group_ids: list[int] = [g["group_id"] for g in groups["data"]]
        
        for group_id in group_ids:
            qusers: list[QUserData] = await QUserData.from_group(api=api, group_id=group_id)
            update_group_member(qusers=qusers)
    
    llm: LLMChatter = llm_registrar.get(settings.CHATTER_LLM_CONFIG_NAME)
    llm.memory.init_memories()


async def send_message(
    api: BotAPI, group_id: int, text: str, voice: bool = True, **kwargs
) -> GroupMessageData | None:
    if voice:
        file = TTS_ROOT / f"voice_{uuid.uuid4().hex}.mp3"
        await voice_query(file=str(file), text=text)
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
        reply_data["data"]["message"].append(
            {
                "type": "text",
                "data": {"text": text}
            }
        )

    return await GroupMessageData.from_group_message(
        data=GroupMessage(reply_data["data"]), from_bot=True, api=api
    )


async def group_chat(
    api: BotAPI,
    message: GroupMessageData,
    split: bool = True,
    voice: bool = True,
) -> bool:
    group_id = message.group_id
    split = False if voice else split
    
    llm: LLMChatter = llm_registrar.get(settings.CHATTER_LLM_CONFIG_NAME)
    response: str | None = await llm.run(message)
    if not response:
        return False
    
    messages: list[GroupMessageData] = []
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
    llm.update_memory(messages)

    return True
