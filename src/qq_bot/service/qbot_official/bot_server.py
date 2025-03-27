from botpy import BotAPI
from botpy.message import GroupMessage, Message
from qq_bot.basekit.models import GroupMessageRecord
from qq_bot.basekit.util import encapsulated_bot_group_reply, encapsulated_group_chat_message
from qq_bot.db.sql.crud.ofcl_group_message_crud import insert_bot_group_message, insert_user_group_message
from qq_bot.service.chat_gpt.chit_chat import chit_chat_gpt
from qq_bot.db.sql.session import LocalSession
from qq_bot.basekit.config import settings
from qq_bot.service.llm_server.llm_registrar import llm_registrar


async def group_chit_chat(api: BotAPI, message: GroupMessage) -> bool:
    user_msg_id = message.id
    group_id = message.group_openid
    user_input = encapsulated_group_chat_message(message)
    # reply = await chit_chat_gpt.run_group(message=user_input)
    reply = await llm_registrar.get(settings.LLM_CAHT_CONFIG_NAME).run(message=user_input)
    
    reply_result = await api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0, 
        msg_id=message.id,
        content=reply
    )
    with LocalSession() as db:
        msg_type = settings.DB_GROUP_TYPE_MAPPING[settings.BOT_COMMAND_GROUP_CHAT]
        user_msg = encapsulated_group_chat_message(message)
        bot_msg = encapsulated_bot_group_reply(reply_result, reply, group_id)
        insert_user_group_message(db=db, message=user_msg, type=msg_type)
        insert_bot_group_message(db=db, user_msg_id=user_msg_id, message=bot_msg)
    return True
