# import ncatbot.utils as utils
# utils.PLUGINS_DIR = "src"

import json
from qq_bot.core.robot.bot import LQBot
from qq_bot.utils.logger import logger
from qq_bot.utils.config import settings


if __name__ == "__main__":
    logger.info(
        "加载配置文件：\n"
        f"{json.dumps(settings.model_dump(), indent=4, ensure_ascii=False)}"
    )
    bot = LQBot(
        bot_uid=settings.BOT_UID,
        ws_url=settings.BOT_WS_URL,
        web_url=settings.BOT_WEBUI_URL,
        token=settings.BOT_TOKEN,
        ws_token=settings.BOT_WS_TOKEN,
        web_token=settings.BOT_WEBUI_TOKEN
    )
    
    bot.run()

