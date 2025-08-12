import asyncio
from ncatbot.core import GroupMessage, PrivateMessage
from qq_bot.core.robot.base import AgentBase
from ncatbot.plugin import CompatibleEnrollment
from qq_bot.core.robot.service import init_agent, update_memory
from qq_bot.core.robot.trigger import (
    group_at_chat,
    group_at_reply,
    group_random_picture,
    group_random_setu,
    group_use_tool,
)
from qq_bot.utils.models import GroupMessageData, QUserData
from qq_bot.utils.logger import logger
from qq_bot.utils.config import settings


class LQBot(AgentBase):
    name = "LQBot"  # 插件名称
    version = "0.1.1"  # 插件版本

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        logger.info(f"加载插件")
        self.bot = CompatibleEnrollment

        # 指令（**检测有顺序区分**）
        self.group_command = [
            group_random_picture,
            group_random_setu,
            group_use_tool,
            group_at_reply,
            group_at_chat,
        ]
        self.register_handlers()

    async def on_load(self):
        await init_agent(self.api)

    def register_handlers(self):
        @self.bot.group_event()
        async def on_group_message(msg: GroupMessage):
            if msg.post_type != "message":
                logger.warning(f"非文本消息，跳过")
                return

            user_msg = await GroupMessageData.from_group_message(data=msg, from_bot=False, api=self.api)
            update_memory(user_msg)
            for handler in self.group_command:
                if await handler(agent=self, message=user_msg, origin_msg=msg):
                    break

        @self.bot.private_event()
        async def on_private_message(msg: PrivateMessage):
            if msg.raw_message == "测试":
                await self.bot.api.post_private_msg(msg.user_id, text="测试成功喵~")

    def run(self):
        self.bot.run()
