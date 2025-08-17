from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings


class SysSetting(BaseSettings):
    # SysSetting 配置不可在yaml配置中修改
    PROJECT_NAME: str = "LQBot"

    CACHE_ROOT: str = "./cache"
    CONFIG_ROOT: str = "./config_example"
    LOG_ROOT: str = "./log"


class NameSetting(BaseSettings):
    WALLPAPER_COMPONENT_NAME: str = "wallpaper provider"
    COMMAND_COMPONENT_NAME: str = "command manager"


class PromptSetting(BaseSettings):
    AGENT_PROMPT: str = ""
    PLUGIN_SCHEDULE_AM_GREET_PROMPT: str = ""


class ServiceSetting(BaseSettings):
    # Bot基本设置
    BOT_UID: str = ""
    BOT_TOKEN: str = ""
    BOT_WS_URL: str = ""
    BOT_WS_TOKEN: str | None = ""
    BOT_WEBUI_URL: str = ""
    BOT_WEBUI_TOKEN: str | None = ""

    # 大模型配置
    BASE_URL: str = ""
    API_KEY: str = ""
    DEFAULT_MODEL: str = ""
    # 对话宽限期，短时间连续对话时内允许用户忽略触发词与bot交互
    CHAT_GRACE_PERIOD: float = 15.0

    HUOSHAN_VOICE_LLM_APPID: str = ""
    HUOSHAN_VOICE_LLM_TOKEN: str = ""
    HUOSHAN_VOICE_LLM_CLUSTER: str = ""

    # 嵌入模型配置
    EMBEDDING_BASE_URL: str = ""
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "bge-m3"

    # 指令集（作为前缀时触发）
    BOT_COMMAND_GROUP_CHAT: list = ["小鱼，", "小鱼"]
    BOT_COMMAND_GROUP_COMMAND: str = "/"

    # 第三方资源收集
    WALLPAPER_API: str = "https://api.anosu.top/img"
    WALLPAPER_R18_API: str = "https://image.anosu.top/pixiv/json"
    AMAP_WEATHER_API: str = "https://restapi.amap.com/v3/weather/weatherInfo"
    AMAP_WEATHER_KEY: str = ""
    HELLDIVERS2_API: str = "https://api.helldivers2.dev/api"
    HELLDIVERS2_CLIENT_NAME: str = "X-Super-Client"
    HELLDIVERS2_CONTACT: str = "X-Super-Contact"

    # 黑白名单（白名单非空时视为开启）
    GROUP_CHAT_BLACK: dict[str, list[int]] = {
        "group_at_trigger": [],
        "group_chat_trigger": [],
        "group_command_trigger": [],
    }
    GROUP_CHAT_WHITE: dict[str, list[int]] = {
        "group_at_trigger": [],
        "group_chat_trigger": [],
        "group_command_trigger": [],
    }


class Setting(SysSetting, NameSetting, PromptSetting, ServiceSetting):
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


def load_config_yaml(path: Path) -> dict:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        return {}

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def load_config() -> Setting:
    settings = Setting()
    extra_config_file = Path(settings.CONFIG_ROOT) / "config.yaml"
    extra_config = load_config_yaml(extra_config_file)
    for key in SysSetting.model_json_schema().get("properties", {}):
        extra_config.pop(key, None)

    return settings.model_copy(update=extra_config)


settings: Setting = load_config()
