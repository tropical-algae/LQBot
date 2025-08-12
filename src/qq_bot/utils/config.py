from pathlib import Path
from typing import Any
from pydantic_settings import BaseSettings
import yaml


class SysSetting(BaseSettings):
    # SysSetting 配置不可在yaml配置中修改
    PROJECT_NAME: str = "LQBot"
    
    CACHE_ROOT: str = "./cache"
    CONFIG_ROOT: str = "./config_example"
    LOG_ROOT: str = "./log"

    # JM_CACHE_ROOT: str = str(Path(CACHE_ROOT) / "jm")
    # TTS_CACHE_ROOT: str = str(Path(CACHE_ROOT) / "tts")
    # RANDOM_PIC_CACHE_ROOT: str = str(Path(CACHE_ROOT) / "wallpaper")
    
    # 额外配置
    # LOCAL_PROMPT_ROOT: str = str(Path(CONFIG_ROOT) / "prompts")
    # EXTRA_CONFIG_FILE: str = str(Path(CONFIG_ROOT) / "ex_config.yaml")
    # JM_OPTION_CONFIG_FILE: str = str(Path(CONFIG_ROOT) / "jm" / "option.yml")
    # COMMAND_CONFIG_FILE: str = str(Path(CONFIG_ROOT) / "components" / "command.yaml")


class DBSetting(BaseSettings):
    # sql db
    SQL_DATABASE_URI: str = ""

    # vector db
    VECTOR_STORE_URL: str = ""
    VECTOR_STORE_TOKEN: str = ""

    ENTITY_VECTOR_STORE_NAME: str = ""
    RELATION_VECTOR_STORE_NAME: str = ""

    VECTOR_SELECT_TOP_K: int = 4
    VECTOR_SELECT_THRESHOLD: float = 0.5

    # minio
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SCCRET_KEY: str = ""
    MINIO_JM_BOCKET_NAME: str = "jm-repertory"
    MINIO_WALLPAPER_BOCKET_NAME: str = "wallpaper"
    MINIO_WALLPAPER_R18_BOCKET_NAME: str = "wallpaper-r18"


class NameSetting(BaseSettings):
    TOOLBOX_COMPONENT_NAME: str = "toolbox"
    WALLPAPER_COMPONENT_NAME: str = "wallpaper provider"
    NEWS_COMPONENT_NAME: str = "news collector"
    COMMAND_COMPONENT_NAME: str = "command manager"
    MINIO_COMPONENT_NAME: str = "minio"
    MYSQL_COMPONENT_NAME: str = "mysql"
    VECTOR_RETRIEVER_COMPONENT_NAME: str = "vector retriever"
    
    # 注册的模型名（名称与LOCAL_PROMPT_ROOT下配置相对应）
    CHATTER_LLM_CONFIG_NAME: str = "bot_chatter"
    TOOLS_LLM_CONFIG_NAME: str = "bot_toolbox"
    RELATION_EXTOR_LLM_CONFIG_NAME: str = "relation_extractor"

class LogSetting(BaseSettings):
    DEBUG: bool = True
    LOG_NAME: str = "log.qqbot.record"
    LOG_FILE_LEVEL: str = "DEBUG"
    LOG_STREAM_LEVEL: str = "INFO"
    LOG_FILE_ENCODING: str = "utf-8"
    LOG_CONSOLE_OUTPUT: bool = False


class ServiceSetting(BaseSettings):
    # Bot基本设置
    BOT_UID: str = ""
    BOT_TOKEN: str = ""
    BOT_WS_URL: str = ""
    BOT_WS_TOKEN: str | None = ""
    BOT_WEBUI_URL: str = ""
    BOT_WEBUI_TOKEN: str | None = ""
    
    # 大模型配置
    GPT_BASE_URL: str = ""
    GPT_API_KEY: str = ""
    
    HUOSHAN_VOICE_LLM_APPID: str = ""
    HUOSHAN_VOICE_LLM_TOKEN: str = ""
    HUOSHAN_VOICE_LLM_CLUSTER: str = ""

    # 嵌入模型配置
    EMBEDDING_BASE_URL: str = ""
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "bge-m3"

    # 指令集（作为前缀时触发）
    BOT_COMMAND_GROUP_CHAT: str = ""
    BOT_COMMAND_GROUP_REPLY: str = ""
    BOT_COMMAND_GROUP_TOOL: str = ""
    BOT_COMMAND_GROUP_JM_CHECK: str = "jm"
    BOT_COMMAND_GROUP_RANDOM_PIC: str = "来点二次元"
    BOT_COMMAND_GROUP_RANDOM_SETU: str = "来点涩图"
    BOT_COMMAND_GROUP_COMMAND: str = "/"

    # 聊天意愿
    CHAT_WILLINGNESS: float = 0.08
    VOICE_WILLINGNESS: float = 0.3

    # 第三方资源收集
    WALLPAPER_API: str = "https://api.anosu.top/img"
    WALLPAPER_R18_API: str = "https://image.anosu.top/pixiv/json"
    NEWS_API: str = ""
    NEWS_SOURCES: dict[str, str] = {}  # 信源中文名与路由名的映射

    # 黑白名单（白名单非空时视为开启）
    GROUP_INSTRUCT_BLACK: dict[str, list[int]] = {
        "group_wallpaper": [],
        "group_wallpaper_r18": [],
        "group_use_tool": [],
        "group_at_reply": [],
        "group_at_chat": [],
    }
    GROUP_INSTRUCT_WHITE: dict[str, list[int]] = {
        "group_wallpaper": [],
        "group_wallpaper_r18": [],
        "group_use_tool": [],
        "group_at_reply": [],
        "group_at_chat": [],
    }


class Setting(SysSetting, DBSetting, NameSetting, LogSetting, ServiceSetting):
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

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def load_config() -> Setting:
    settings = Setting()
    extra_config_file = Path(settings.CONFIG_ROOT) / "ex_config.yaml"
    extra_config = load_config_yaml(extra_config_file)
    for key in SysSetting.model_json_schema().get("properties", {}).keys():
        extra_config.pop(key, None)
    
    return settings.model_copy(update=extra_config)


settings: Setting = load_config()
