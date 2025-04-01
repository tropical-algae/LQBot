import ast
from ncatbot.core import BotAPI, BotClient, GroupMessage, PrivateMessage
from qq_bot.core.agent.base import AgentBase
from ncatbot.plugin import BasePlugin

from qq_bot.core.tool_manager.tool_registrar import ToolRegistrar
from qq_bot.utils.logging import logger
from qq_bot.core.agent.agent_command import group_at_chat, group_random_picture, group_random_setu, group_use_tool
from qq_bot.core.agent.agent_server import group_random_chat
from ncatbot.plugin import CompatibleEnrollment
from ncatbot.utils.time_task_scheduler import TimeTaskScheduler
from ncatbot.plugin.event import EventBus


class QAgent(AgentBase):
    name = "QAgent" # 插件名称
    version = "0.1.0" # 插件版本
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        logger.info(f"加载插件")
        
        self.tools = ToolRegistrar(agent=self)

        self.bot = CompatibleEnrollment
        
        # 命令方法（有序检测）
        self.group_command = [group_random_picture, group_random_setu, group_use_tool, group_at_chat]
        
        self.register_handlers()

    def register_handlers(self):
        @self.bot.group_event()
        async def on_group_message(msg: GroupMessage):
            is_replied: bool = False
            for handler in self.group_command:
                if await handler(agent=self, message=msg):
                    is_replied = True
                    break

            if not is_replied:
                await group_random_chat(self.api, msg, 0.15, need_split=True)

        @self.bot.private_event()
        async def on_private_message(msg: PrivateMessage):
            if msg.raw_message == "测试":
                await self.bot.api.post_private_msg(msg.user_id, text="测试成功喵~")

    def run(self):
        self.bot.run()

