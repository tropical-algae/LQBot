from enum import Enum
from typing import Annotated

import httpx

from lqbot.core.agent.base import AgentBase, InformationBase, ToolBase
from lqbot.utils.config import settings
from lqbot.utils.logger import logger
from lqbot.utils.models import AgentMessage


class WeatherType(str, Enum):
    REALTIME = "实时天气"
    FORECAST = "天气预报"


class WeatherCastInfo(InformationBase):
    date: str
    week: str
    dayweather: str
    nightweather: str
    daytemp: str
    nighttemp: str
    daywind: str
    nightwind: str
    daypower: str
    nightpower: str
    daytemp_float: str
    nighttemp_float: str

    def summary(self) -> str:
        return (
            f"{self.date}（week {self.week}）天气预报如下："
            f"白天{self.dayweather}，气温约{self.daytemp}摄氏度，吹{self.daywind}风，风力{self.daypower}级；"
            f"夜间{self.nightweather}，气温约{self.nighttemp}摄氏度，吹{self.nightwind}风，风力{self.nightpower}级。"
        )


class WeatherForecastInfo(InformationBase):
    city: str
    adcode: str
    province: str
    reporttime: str
    casts: list[WeatherCastInfo]

    def summary(self) -> str:
        return (
            f"当前天气预报信息的更新时间为{self.reporttime}，以下是({self.province}){self.city}的天气预报：\n"
            + "\n".join(cast.summary() for cast in self.casts)
        )


class WeatherLiveInfo(InformationBase):
    province: str
    city: str
    adcode: str
    weather: str
    temperature: str
    winddirection: str
    windpower: str
    humidity: str
    reporttime: str

    def summary(self):
        return (
            f"当前时间{self.reporttime}，({self.province}){self.city}实时天气如下："
            f"{self.weather}，气温{self.temperature}摄氏度，湿度{self.humidity}%。"
            f"风向{self.winddirection}，风力{self.windpower}级。"
        )


async def get_weather_info(location: str, weather_type: WeatherType) -> str:
    # 定义 extensions 与目标解析模型的映射
    extensions_map: dict[WeatherType, tuple[str, str, type[InformationBase]]] = {
        WeatherType.FORECAST: ("all", "forecasts", WeatherForecastInfo),
        WeatherType.REALTIME: ("base", "lives", WeatherLiveInfo),
    }

    extensions, key, model_class = extensions_map.get(weather_type, ("base", None, None))
    if not key or not model_class:
        return "不支持的天气类型请求"

    url = f"{settings.AMAP_WEATHER_API}?key={settings.AMAP_WEATHER_KEY}&extensions={extensions}&city={location}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data: dict = response.json()

        if data.get("status") != "1":
            return "天气数据获取失败"

        items: list | None = data.get(key)
        if not items:
            return "未查询到有效的天气信息"

        info = model_class.model_validate(items[0])
        return info.summary()

    except Exception as err:
        logger.error(f"天气信息获取错误: {err}")
        return "无法获取该地区的天气信息"


class WeatherTool(ToolBase):
    __tool_name__ = "weather_tool"
    __tool_description__ = (
        "工具作用：获取某地区的天气信息\n触发方式：当用户询问天气时请调用\n"
    )
    __is_async__ = True

    @staticmethod
    async def a_tool_function(
        weather_type: Annotated[WeatherType, "要了解的天气信息类型"],
        location: Annotated[str, "要查询的省份或地区"],
    ) -> str:
        weather_type = WeatherType(weather_type)
        info = await get_weather_info(location=location, weather_type=weather_type)

        return info

    @staticmethod
    def tool_post_processing_function(
        agent: AgentBase, agent_message: AgentMessage
    ) -> None:
        _ = agent
        agent_message.can_split = False
