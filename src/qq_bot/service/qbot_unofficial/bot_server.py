import random
from ncatbot.core import GroupMessage, BotAPI
from qq_bot.basekit.models import GroupMessageRecord
from qq_bot.basekit.util import encapsulated_bot_group_reply, encapsulated_group_chat_message, get_data_from_message
from qq_bot.db.sql.crud.unofcl_group_message_crud import insert_group_message
from qq_bot.service.chat_gpt.chit_chat import chit_chat_gpt
from qq_bot.db.sql.session import LocalSession
from qq_bot.basekit.config import settings
from qq_bot.service.llm_server.llm_registrar import llm_registrar
from qq_bot.basekit.logging import logger
from qq_bot.service.llm_server.llms import LLMChatter


async def group_random_chat(api: BotAPI, message: GroupMessage, prob: float) -> bool:
    reply_message: GroupMessageRecord | None = None
    llm: LLMChatter = llm_registrar.get(settings.LLM_CAHT_CONFIG_NAME)
    
    if message.post_type == "message":
        
        # 概率触发聊天
        if random.random() < prob:
            logger.info("触发随机闲聊")
            
            msg_obj = encapsulated_group_chat_message(message)
            reply: str | None = await llm.run(message=msg_obj)
            
            if reply:
                reply_result: dict = await message.api.post_group_msg(
                    group_id=msg_obj.group_id,
                    text=reply
                )
                if reply_result["status"] == "ok" and reply_result["data"]:
                    reply_data = await api.get_msg(reply_result["data"].get("message_id", -1))
                    
                    if reply_data["status"] == "ok" and reply_data["data"]:
                        reply_message = encapsulated_group_chat_message(
                            GroupMessage(reply_data["data"])
                        )
    
        # 更新聊天LLM历史记录
        llm.insert_and_update_history_message(
            group_id=message.group_id,
            user_message=get_data_from_message(message.message, "text").get("text", "").strip(),
            llm_message=reply_message.content if reply_message else None
        )

        # 存储聊天信息到SQL
        with LocalSession() as db:
            insert_group_message(
                db=db, 
                message=encapsulated_group_chat_message(message), 
                is_bot=False
            )
            if reply_message:
                insert_group_message(
                    db=db, 
                    message=reply_message, 
                    is_bot=True
                )
        return True if reply_message else False
    return False


