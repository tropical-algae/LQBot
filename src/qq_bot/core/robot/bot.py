import time

from collections import defaultdict
from ncatbot.core import GroupMessage, PrivateMessage
from ncatbot.plugin import CompatibleEnrollment
from ncatbot.core import BotAPI, BotClient, GroupMessage, PrivateMessage
from ncatbot.utils.config import config
from ncatbot.utils import get_log

from qq_bot.core.robot.handlers.sender import group_chat
from qq_bot.core.robot.trigger import (
    group_at_trigger,
    group_chat_trigger,
    group_command_trigger,
)
from qq_bot.utils.models import GroupMessageData, QUserData
# from qq_bot.utils.logger import logger
from qq_bot.utils.config import settings


logger = get_log()


class LQBot:

    def __init__(
        self, 
        bot_uid: str,
        ws_url: str, 
        web_url: str, 
        token: str, 
        ws_token: str | None = None,
        web_token: str | None = None
    ) -> None:

        logger.info(f"加载工具集")
        self.bot = BotClient()
        
        config.set_bot_uin(bot_uid)
        config.set_root(bot_uid)
        config.set_ws_uri(ws_url)
        config.set_webui_uri(web_url)
        config.set_token(token)
        
        if ws_token:
            config.set_ws_token(ws_token)
        if web_token:
            config.set_webui_token(web_token)

        # 指令（**检测有顺序区分**）
        self.group_command = [
            group_command_trigger,
            group_at_trigger,
            group_chat_trigger
        ]
        self.register_handlers()
        # 用于连贯对话，短期内用户重复对话可以免去触发词
        self.session_timestamp: dict[str, dict[str, float]] = defaultdict(dict)

    def register_handlers(self):
        @self.bot.group_event()
        async def on_group_message(msg: GroupMessage):
            if msg.post_type != "message":
                logger.warning(f"非文本消息，跳过")
                return

            user_msg = await GroupMessageData.from_group_message(data=msg, from_bot=False, api=self.bot.api)
            
            group_id = user_msg.group_id
            sender_id = user_msg.sender.id
            sender_name = user_msg.sender.nickname
            msg_abs = f"{user_msg.content[:7]}..."
            logger.info(f"[GROUP {group_id}][{sender_name}]:\t{msg_abs}")
            
            for handler in self.group_command:
                if await handler(bot=self.bot, message=user_msg, origin_msg=msg):
                    self.session_timestamp[group_id][sender_id] = time.time()
                    return

            last_time = self.session_timestamp[group_id].get(sender_id)
            if last_time and (time.time() - last_time < settings.CHAT_GRACE_PERIOD):
                await group_chat(api=self.bot.api, message=user_msg)
                self.session_timestamp[group_id][sender_id] = time.time()
                logger.info(f"[GROUP {group_id}] 触发连续对话")


        @self.bot.private_event()
        async def on_private_message(msg: PrivateMessage):
            if msg.raw_message == "测试":
                await self.bot.api.post_private_msg(msg.user_id, text="测试成功喵~")

    def run(self):
        self.bot.run()
