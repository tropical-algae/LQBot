import ncatbot.utils.literals as literals
literals.PLUGINS_DIR = "src"


from ncatbot.utils.config import config
from ncatbot.core import BotAPI, BotClient, GroupMessage, PrivateMessage



if __name__ == "__main__":
    
    config.set_bot_uin("3974509995")  # 设置 bot qq 号 (必填)
    config.set_root("3974509995")  # 设置 bot 超级管理员账号 (建议填写)
    config.set_ws_uri("ws://localhost:3001")  # 设置 napcat websocket server 地址
    config.set_token("")  # 设置 token (napcat 服务器的 token)
    bot = BotClient()
    bot.run()
