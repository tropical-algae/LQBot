import botpy
from botpy.message import GroupMessage, Message
from qq_bot.basekit.logging import logger
from qq_bot.service.qq_bot.bot_server import group_chit_chat
from qq_bot.service.qq_bot.bot_command import group_insert, group_jm_pic, group_select

class QQBotClient(botpy.Client):
    async def on_ready(self):
        self.group_command = [group_select, group_insert, group_jm_pic]
        logger.info(f"robot 「{self.robot.name}」 on_ready!")

    async def command_group_replay(self, message: GroupMessage) -> bool:
        for handler in self.group_command:
            if await handler(api=self.api, message=message):
                return True
        return False

    async def normal_group_reply(self, message: GroupMessage):
        message.content = message.content.strip()
        await group_chit_chat(api=self.api, message=message)
        return True

    # async def on_at_message_create(self, message: Message):
    #     await self.api.get_message(channel_id="xxxx", message_id="xxxx")
    
    async def on_message_create(self, message: Message):
        print(message)
    
    async def on_group_at_message_create(self, message: GroupMessage):
        logger.info(f"USER[{message.author.member_openid}]: {message.content}")

        result = await self.command_group_replay(message=message)
        if not result:
            result = await self.normal_group_reply(message=message)
