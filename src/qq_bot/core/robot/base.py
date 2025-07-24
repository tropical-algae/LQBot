from ncatbot.plugin import BasePlugin
from ncatbot.core import BotClient


class AgentBase(BasePlugin):
    def __init__(self, **kwargs):
        self.bot: BotClient | None = None

        super().__init__(**kwargs)

    async def on_load(self):
        pass

    def register_handlers(self):
        pass

    def run(self):
        pass
