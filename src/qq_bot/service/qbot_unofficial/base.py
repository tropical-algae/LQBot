import ast
from ncatbot.core import BotAPI, BotClient, GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin
from ncatbot.utils.config import config
from qq_bot.basekit.logging import logger
from qq_bot.service.qbot_unofficial.bot_command import group_at_chat, group_random_picture, group_random_setu
from qq_bot.service.qbot_unofficial.bot_server import group_random_chat


class QQBotClient(BasePlugin):
    def __init__(self):
        config.set_bot_uin("3974509995")  # 设置 bot qq 号 (必填)
        config.set_root("3974509995")  # 设置 bot 超级管理员账号 (建议填写)
        config.set_ws_uri("ws://localhost:3001")  # 设置 napcat websocket server 地址
        config.set_token("")  # 设置 token (napcat 服务器的 token)
        self.bot = BotClient()
        self.api = BotAPI()
        
        self.group_command = [group_random_picture, group_random_setu, group_at_chat]
        
        self.register_handlers()
    
    # def on_load(self):
    #     self.add_scheduled_task(
    #         job_func=self.zaoba, 
    #         name="早八问候", 
    #         interval="08:00",
    #         max_runs=10, 
    #         args=("早八人", ),
    #     )
    

    def register_handlers(self):
        @self.bot.group_event()
        async def on_group_message(msg: GroupMessage):
            is_replied: bool = False
            for handler in self.group_command:
                if await handler(api=self.api, message=msg):
                    is_replied = True
                    break
            
            if not is_replied:
                await group_random_chat(self.api, msg, 0.05)

        @self.bot.private_event()
        async def on_private_message(msg: PrivateMessage):
            if msg.raw_message == "测试":
                await self.bot.api.post_private_msg(msg.user_id, text="测试成功喵~")

    def run(self):
        self.bot.run()

