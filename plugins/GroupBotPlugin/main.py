import asyncio
import random
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import ClassVar

from ncatbot.core import GroupMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from lqbot import __version__ as __version__
from lqbot.core.robot.handlers.sender import group_chat
from lqbot.core.robot.trigger import (
    group_at_trigger,
    group_chat_trigger,
    group_command_trigger,
)
from lqbot.utils.config import settings
from lqbot.utils.logger import logger
from lqbot.utils.models import GroupMessageData, QUserData
from lqbot.utils.util import handle_task_result

bot = CompatibleEnrollment


class GroupBotPlugin(BasePlugin):
    name = "GroupBotPlugin"  # 插件名
    version = __version__  # 插件版本

    async def on_load(self):
        logger.info(f"{self.name}({self.version}) 插件已加载")
        # 指令（**检测有顺序区分**）
        self.group_command = [group_command_trigger, group_at_trigger, group_chat_trigger]
        # 用于连贯对话，短期内用户重复对话可以免去触发词
        self.session_timestamp: dict[int, dict[int, float]] = defaultdict(dict)

    def _is_interaction_recent(self, group_id: int, sender_id: int) -> bool:
        last_time = self.session_timestamp[group_id].get(sender_id)
        if last_time and (time.time() - last_time < settings.CHAT_GRACE_PERIOD):
            self.session_timestamp[group_id][sender_id] = time.time()
            logger.info(f"[GROUP {group_id}] 触发连续对话")
            return True
        return False

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        if msg.post_type != "message":
            logger.warning("非文本消息，跳过")
            return

        user_msg = await GroupMessageData.from_group_message(
            data=msg, from_bot=False, api=self.api
        )

        group_id = user_msg.group_id
        sender_id = user_msg.sender.id
        sender_name = user_msg.sender.nickname
        msg_abs = f"{user_msg.content[:7]}..."
        logger.info(f"[GROUP {group_id}][{sender_name}]:\t{msg_abs}")

        for handler in self.group_command:
            if await handler(api=self.api, message=user_msg, origin_msg=msg):
                self.session_timestamp[group_id][sender_id] = time.time()
                return

        # 免触发词判定
        if self._is_interaction_recent(group_id=group_id, sender_id=sender_id):
            await group_chat(api=self.api, message=user_msg)
