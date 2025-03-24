import botpy
from alembic import command
from alembic.config import Config

from qq_bot.common.config import settings
from qq_bot.common.logging import logger
from qq_bot.service.qq_bot.base import QQBotClient


def run() -> None:
    # command.upgrade(Config("alembic.ini"), "head")
    intents = botpy.Intents(public_messages=True)
    client = QQBotClient(intents=intents)
    client.run(appid=settings.QQBOT_APPID, secret=settings.QQBOT_SECRET)


if __name__ == "__main__":
    run()
