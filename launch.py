import json

from lqbot.core.robot.bot import LQBot
from lqbot.utils.config import settings
from lqbot.utils.logger import logger

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
        web_token=settings.BOT_WEBUI_TOKEN,
    )

    bot.run()
