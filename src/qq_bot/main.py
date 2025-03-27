import botpy

from qq_bot.basekit.config import settings
from qq_bot.basekit.logging import get_logger_absolute_path, get_system_logger_config, logger
from qq_bot.service import qbot_official, qbot_unofficial


#*
# Chat Model 解析时添加is bot
# 为llm聊天地history添加用户识别
# #

def run_official() -> None:
    intents = botpy.Intents(public_messages=True)
    client = qbot_official.QQBotClient(
        intents=intents, 
        # log_config=get_system_logger_config(get_logger_absolute_path("qbot-system")), 
        timeout=20
    )
    client.run(appid=settings.QQBOT_APPID, secret=settings.QQBOT_SECRET)

def run_unofficial() -> None:
    client = qbot_unofficial.QQBotClient()
    client.run()
    

if __name__ == "__main__":
    run_unofficial()
