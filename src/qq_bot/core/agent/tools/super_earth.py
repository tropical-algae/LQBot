
import asyncio
from enum import Enum
from typing import List, Annotated, Optional
from dateutil import parser
import httpx
from datetime import date as dt_date, datetime

from pydantic import BaseModel

from qq_bot.core.agent.tools.base import ToolBase
from qq_bot.utils.models import AgentMessage
from qq_bot.utils.util import normalize_date
from qq_bot.utils.config import settings


class NewsSubject(str, Enum):
    DISPATCHES = "前线讯息"
    SITUATION = "战况与局势"


class Dispatches(BaseModel):
    id: int
    published: str
    type: int
    message: str
    
    def summary(self) -> str:
        return f"{self.published} 讯息: {self.message}"


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

    async def get_dispatches(self, target_date: dt_date) -> str:
        url = f"{self.BASE_URL}/dispatches"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            # 转换并查找
            same_day_items = []
            data = response.json()
            for item in data:
                pub_dt = datetime.fromisoformat(item["published"].replace("Z", "+00:00"))
                if pub_dt.date() == target_date:
                    same_day_items.append(Dispatches(**item))

            if same_day_items:
                result = same_day_items
            else:
                current_item = max(data, key=lambda x: datetime.fromisoformat(x["published"].replace("Z", "+00:00")))
                result = [Dispatches(**current_item)]
            
            return "\n".join([msg.summary() for msg in result])


hd_client = HelldiversAPIClient(
    client_name=settings.HELLDIVERS2_CLIENT_NAME, 
    contact=settings.HELLDIVERS2_CONTACT
)


# async def run():
#     result = await hd_client.get_dispatches(normalize_date("2025/8/19"))
#     print(result)

# asyncio.run(run())


class SuperEarthTool(ToolBase):
    __tool_name__ = "super_earth_tool"
    __tool_description__ = "若用户想了解“超级地球”的消息，请调用。注意，必须是有关“超级地球”的信息"
    __is_async__ = True
    
    async def a_tool_function(
        news_type: Annotated[Optional[NewsSubject], "用户想了解的消息的主题"],
        date: Annotated[str, "信息的日期，例如 2025-08-20。可以不提供日期"] = None,
    ) -> None:
        news_type = NewsSubject(news_type)
        target_date: dt_date = normalize_date(date)
        
        if news_type == NewsSubject.DISPATCHES:
            return await hd_client.get_dispatches(target_date=target_date)
        
        if news_type == NewsSubject.SITUATION:
            pass
        
        return "不太清楚呢"
    
    def tool_post_processing_function(agent_message: AgentMessage) -> None:
        agent_message.can_split = False
