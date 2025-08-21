import asyncio
import random
from datetime import datetime, timedelta
from typing import ClassVar

from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from lqbot import __version__ as __version__
from lqbot.core.robot.handlers.sender import group_chat
from lqbot.utils.config import settings
from lqbot.utils.logger import logger
from lqbot.utils.models import GroupMessageData, QUserData
from lqbot.utils.util import handle_task_result

bot = CompatibleEnrollment


class SchedulePlugin(BasePlugin):
    name = "SchedulePlugin"  # 插件名
    version = __version__  # 插件版本

    subscribed_groups: ClassVar[list[int]] = []

    async def on_load(self):
        # 注册到工具
        logger.info(f"{self.name}({self.version}) 插件已加载")

        self.schedules: dict
        self.add_scheduled_task(
            job_func=self.refresh_daily_greet,
            name="每日定时任务规划",
            interval="00:01",
        )

    @staticmethod
    def _get_random_am(time_from: int, time_to: int) -> str:
        today = datetime.now().date()  # 今天的日期
        start_seconds = time_from * 3600
        end_seconds = time_to * 3600
        random_seconds = random.randint(start_seconds, end_seconds)
        random_time = datetime.combine(today, datetime.min.time()) + timedelta(
            seconds=random_seconds
        )
        return random_time.strftime("%Y-%m-%d %H:%M:%S")

    def refresh_daily_greet(self):
        greet_am = self._get_random_am(7, 9)
        prompt = f"当前时间：{greet_am}\n{settings.PLUGIN_SCHEDULE_AM_GREET_PROMPT}"

        self.add_scheduled_task(
            job_func=self.greet,
            name="早晨打招呼",
            interval=greet_am,
            args=(prompt,),
        )

    def greet(self, prompt: str) -> None:
        messages: GroupMessageData = [
            GroupMessageData(
                id=-1,
                content=prompt,
                group_id=group,
                sender=QUserData(id=-1),
                from_bot=False,
                send_time=datetime.now(),
            )
            for group in self.subscribed_groups
        ]

        loop = asyncio.get_event_loop()

        for message in messages:
            task = loop.create_task(
                group_chat(api=self.api, message=message, use_agent=False)
            )
            task.add_done_callback(handle_task_result)
