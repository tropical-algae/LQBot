from ncatbot.core import BotClient
from ncatbot.utils.config import config

from lqbot.utils.config import settings
from lqbot.utils.logger import logger


class LQBot:
    def __init__(
        self,
        bot_uid: str,
        ws_url: str,
        web_url: str,
        token: str,
        ws_token: str | None = None,
        web_token: str | None = None,
    ) -> None:
        logger.info("加载工具集")
        self.bot = BotClient()

        config.set_bot_uin(bot_uid)
        config.set_root(bot_uid)
        config.set_ws_uri(ws_url)
        config.set_webui_uri(web_url)
        config.set_token(token)

        if ws_token:
            config.set_ws_token(ws_token)
        if web_token:
            config.set_webui_token(web_token)

    def run(self):
        self.bot.run()
