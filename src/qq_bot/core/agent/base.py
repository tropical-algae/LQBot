from ncatbot.plugin import BasePlugin
from ncatbot.core import BotClient, BotAPI
from ncatbot.utils.time_task_scheduler import TimeTaskScheduler
from ncatbot.plugin.event import EventBus
from qq_bot.core.tool_manager.base import ToolRegistrarBase



class AgentBase(BasePlugin):
    
    def __init__(self, **kwargs):
        self.bot: BotClient | None = None
        self.api: BotAPI | None = None
        self.tools: ToolRegistrarBase | None = None
        super().__init__(**kwargs)

    async def on_load(self):
        pass
    #     self.add_scheduled_task(
    #         job_func=self.zaoba, 
    #         name="早八问候", 
    #         interval="08:00",
    #         max_runs=10, 
    #         args=("早八人", ),
    #     )
    
    # def zaoba(self):
    #     print("asd")

    def register_handlers(self):
        pass

    def run(self):
        pass

