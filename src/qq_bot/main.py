import botpy

from qq_bot.basekit.config import settings
from qq_bot.basekit.logging import get_logger_absolute_path, get_system_logger_config, logger
from qq_bot.service.qq_bot.base import QQBotClient


def run() -> None:
    intents = botpy.Intents(public_messages=True)
    client = QQBotClient(
        intents=intents, 
        # log_config=get_system_logger_config(get_logger_absolute_path("qbot-system")), 
        timeout=20
    )
    client.run(appid=settings.QQBOT_APPID, secret=settings.QQBOT_SECRET)


if __name__ == "__main__":
    run()
