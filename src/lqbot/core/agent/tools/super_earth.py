# ruff: noqa: N815

from datetime import date as dt_date
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

import httpx
from dateutil import parser

from lqbot.core.agent.base import AgentBase, InformationBase, ToolBase
from lqbot.utils.config import settings
from lqbot.utils.decorator import exception_handling
from lqbot.utils.logger import logger
from lqbot.utils.models import AgentMessage


class SEInfoType(str, Enum):
    DISPATCHES = "新闻"
    SITUATION = "战况"


class SEDispatches(InformationBase):
    id: int
    published: str
    type: int
    message: str

    def summary(self, **kwargs) -> str:
        _ = kwargs
        return f"{self.published} 新闻: {self.message}"


class SEWarStatistics(InformationBase):
    missionsWon: int
    missionsLost: int
    missionTime: int
    terminidKills: int
    automatonKills: int
    illuminateKills: int
    bulletsFired: int
    bulletsHit: int
    timePlayed: int
    deaths: int
    revives: int
    friendlies: int
    missionSuccessRate: int
    accuracy: int
    playerCount: int

    def summary(self, **kwargs) -> str:
        _ = kwargs
        return (
            f"截至目前，已完成任务 {self.missionsWon} 次，失败 {self.missionsLost} 次，"
            f"成功率 {self.missionSuccessRate}% 。累计击杀终结虫 {self.terminidKills} 只，"
            f"机器人 {self.automatonKills} 台，光能族 {self.illuminateKills} 名。友军误伤 {self.friendlies} 名。"
            f"累计消耗弹药 {self.bulletsFired} 发，命中 {self.bulletsHit} 发，准确率 {self.accuracy}%。"
            f"当前活跃的绝地遣兵人数 {self.playerCount} 人。"
        )


class SEWarSituation(InformationBase):
    started: str
    ended: str
    now: str
    clientVersion: str
    factions: list[str]
    impactMultiplier: float
    statistics: SEWarStatistics

    def summary(self, **kwargs) -> str:
        _ = kwargs
        return f"超级地球战报如下：\n{self.statistics.summary()}"


def normalize_date(user_input: str | None) -> Any:
    if not user_input:
        return None
    try:
        parsed = parser.parse(user_input)
        return parsed.date()
    except Exception:
        return None


class HelldiversAPIClient:
    BASE_URL = settings.HELLDIVERS2_API

    def __init__(self, client_name: str, contact: str, timeout: float = 10.0):
        self.headers = {
            "accept": "application/json",
            "X-Super-Client": client_name,
            "X-Super-Contact": contact,
            "Accept-Language": "zh-Hans",
        }
        self.timeout = timeout

    @exception_handling(default_return="不清楚超级地球的新闻")
    async def get_dispatches(self, date: dt_date | None = None) -> str:
        """获取超级地球的新闻

        Args:
            date (dt_date | None, optional): 查询的日期，当空时默认取当天. Defaults to None.

        Returns:
            str: 目标日期的日志
        """
        url = f"{self.BASE_URL}/v2/dispatches"
        target_date = datetime.date(datetime.now()) if date is None else date

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()

            # 解析日期，获取day匹配的数据
            same_day_items = []
            data = response.json()
            for item in data:
                pub_dt = datetime.fromisoformat(item["published"].replace("Z", "+00:00"))
                if pub_dt.date() == target_date:
                    same_day_items.append(SEDispatches(**item))

            # 无匹配数据时取最新
            if same_day_items:
                result = same_day_items
            else:
                current_item = max(
                    data,
                    key=lambda x: datetime.fromisoformat(
                        x["published"].replace("Z", "+00:00")
                    ),
                )
                result = [SEDispatches(**current_item)]

            return "\n".join([msg.summary() for msg in result])

    @exception_handling(default_return="不清楚超级地球的战况")
    async def get_situation(self) -> str:
        """获取超级地球战况

        Returns:
            str: 超级地球战况
        """
        url = f"{self.BASE_URL}/v1/war"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()

            situation = SEWarSituation.model_validate(data)
            return situation.summary()


hd_client = HelldiversAPIClient(
    client_name=settings.HELLDIVERS2_CLIENT_NAME, contact=settings.HELLDIVERS2_CONTACT
)


class SuperEarthTool(ToolBase):
    __tool_name__ = "super_earth_tool"
    __tool_description__ = "查询超级地球的信息（超级地球是固有名词）"
    __is_async__ = True

    @staticmethod
    async def a_tool_function(
        info_type: Annotated[SEInfoType, "信息的类型"],
        date: Annotated[
            str | None,
            "信息的日期。当提供了时间信息时，要结合当前时间分析真正要查询的日期",
        ] = None,
    ) -> str:
        info_type = SEInfoType(info_type)
        target_date: dt_date = normalize_date(date) or dt_date.today()

        if info_type == SEInfoType.DISPATCHES:
            return await hd_client.get_dispatches(date=target_date)

        if info_type == SEInfoType.SITUATION:
            return await hd_client.get_situation()

        return "不太清楚超级地球的消息"

    @staticmethod
    def tool_post_processing_function(
        agent: AgentBase, agent_message: AgentMessage
    ) -> None:
        _ = agent
        agent_message.can_split = False
