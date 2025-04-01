import asyncio
import random
from ncatbot.core import GroupMessage, BotAPI
from qq_bot.core.agent.base import AgentBase
from qq_bot.utils.models import GroupMessageRecord
from qq_bot.utils.util_text import auto_split_sentence, get_data_from_message, language_classifity, typing_time_calculate
from qq_bot.conn.sql.crud.group_message_crud import insert_group_message, insert_group_messages
from qq_bot.conn.sql.session import LocalSession
from qq_bot.utils.config import settings
from qq_bot.core.llm_manager.llm_registrar import llm_registrar
from qq_bot.utils.logging import logger
from qq_bot.core.llm_manager.llms.chatter import LLMChatter


async def send_msg_2_group(api: BotAPI, group_id: int, text: str, **kwargs) -> GroupMessageRecord | None:
    result: dict = await api.post_group_msg(group_id=group_id, text=text, **kwargs)
    if result.get("status") != "ok" or not result.get("data"):
        return None
    msg_id = result["data"].get("message_id", -1)
    reply_data = await api.get_msg(msg_id)
    if reply_data.get("status") != "ok" or not reply_data.get("data"):
        return None
    return await GroupMessageRecord.from_group_message(GroupMessage(reply_data["data"]), True)

async def group_random_chat(
    api: BotAPI, 
    message: GroupMessage, 
    prob: float, 
    need_split: bool = True
) -> bool:
    if message.post_type != "message":
        return False

    # 概率触发聊天
    real_prob = random.random()
    if real_prob < prob:
        logger.info(f"触发闲聊 -> 概率[{prob:.2f}({real_prob:.2f}) / 1.0]")
        
        reply_msg: GroupMessageRecord | None = None
        reply_splited_msgs: list[GroupMessageRecord] = []
        
        llm: LLMChatter = llm_registrar.get(settings.CHATTER_LLM_CONFIG_NAME)
        user_message = await GroupMessageRecord.from_group_message(message, False)
        reply: str | None = await llm.run(user_message)

        if not reply:
            return False

        if need_split:
            language = language_classifity(reply)
            replies: list[str] = auto_split_sentence(reply, language)

            for text in replies:
                await asyncio.sleep(typing_time_calculate(text, language))
                bot_reply = await send_msg_2_group(api, message.group_id, text)
                if bot_reply:
                    reply_splited_msgs.append(bot_reply)
        else:
            await asyncio.sleep(typing_time_calculate(reply, language))
            reply_msg = await send_msg_2_group(api, message.group_id, reply)

        # 存储聊天信息到SQL
        with LocalSession() as db:
            all_messages = [user_message]

            if need_split and reply_splited_msgs:
                all_messages += reply_splited_msgs
            elif reply_msg:
                all_messages.append(reply_msg)
            
            insert_group_messages(db=db, messages=all_messages)
            
            is_saved = (need_split and reply_splited_msgs) or (not need_split and reply_msg)
            if is_saved:
                logger.info(f"聊天记录已存储")
            else:
                logger.error(f"聊天记录存储失败")
            
            return is_saved
    return False
        
