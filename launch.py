import json
import ncatbot.utils.literals as literals
literals.PLUGINS_DIR = "src"

from ncatbot.utils.config import config
from ncatbot.core import BotAPI, BotClient, GroupMessage, PrivateMessage

from qq_bot.utils.logging import logger
from qq_bot.utils.config import settings


if __name__ == "__main__":
    
    logger.info(f"加载配置文件：\n{json.dumps(settings.model_dump(), indent=4, ensure_ascii=False)}")
    
    config.set_bot_uin(settings.BOT_UID)  # 设置 bot qq 号 (必填)
    config.set_root(settings.BOT_UID)  # 设置 bot 超级管理员账号 (建议填写)
    config.set_ws_uri(settings.BOT_WS_URL)  # 设置 napcat websocket server 地址
    config.set_token("")  # 设置 token (napcat 服务器的 token)
    
    bot = BotClient()
    bot.run()
