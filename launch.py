import ncatbot.utils as utils
utils.PLUGINS_DIR = "src"

import json

from ncatbot.utils.config import config
from ncatbot.core import BotAPI, BotClient, GroupMessage, PrivateMessage

from qq_bot.utils.logging import logger
from qq_bot.utils.config import settings


if __name__ == "__main__":
    logger.info(
        "加载配置文件：\n"
        f"{json.dumps(settings.model_dump(), indent=4, ensure_ascii=False)}"
    )

    config.set_bot_uin(settings.BOT_UID)
    config.set_root(settings.BOT_UID)
    config.set_ws_uri(settings.BOT_WS_URL)
    config.set_token("")

    bot = BotClient()
    bot.run()
