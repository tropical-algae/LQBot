import secrets

from pydantic_settings import BaseSettings


class SysSetting(BaseSettings):
    PROJECT_NAME: str = "QQ BOT"
    DEBUG: bool = True
    QQBOT_APPID: str = ""
    QQBOT_SECRET: str = ""
    # PUBLIC_IP_ADDRESS: str = ""
    
    VECTOR_QUERY_GPT_PROMPT: str = "prompts/vector_query_prompt.yaml"
    CHIT_CHAT_GPT_PROMPT: str = "prompts/chit_chat_prompt.yaml"
    
    JM_CACHE_ROOT: str = "./cache/jm"
    JM_OPTION: str = "./configs/jm/option.yml"
    
    LOCAL_PROMPT_ROOT: str = "./configs/llm"
    
    RANDOM_PIC_CACHE_ROOT: str = "./cache/random_pic"
    RANDOM_PIC_API: str = ""
    

class DBSetting(BaseSettings):
    
    # sql db
    SQL_DATABASE_URI: str = ""

    SECRET_KEY: str = secrets.token_urlsafe(32)
    DEFAULT_SUPERUSER: str = "admin"
    DEFAULT_SUPERUSER_PASSWD: str = "admin"
    
    # sql data
    BOT_COMMAND_GROUP_CHAT: str = "聊天"
    BOT_COMMAND_GROUP_QUERY: str = "询问"
    BOT_COMMAND_GROUP_RECORD: str = "悄悄话"
    BOT_COMMAND_GROUP_JM_CHECK: str = "jm"
    BOT_COMMAND_GROUP_RANDOM_PIC: str = "来点二次元"
    
    DB_GROUP_TYPE_MAPPING: dict[str, str] = {
        BOT_COMMAND_GROUP_CHAT: "group_chat",
        BOT_COMMAND_GROUP_QUERY: "group_within_query",
        BOT_COMMAND_GROUP_RECORD: "group_within_record"
    }
    
    # vector db
    VECTOR_STORE_URL: str = ""
    VECTOR_STORE_TOKEN: str = ""
    VECTOR_STORE_NAME: str = ""
    
    VECTOR_SELECT_TOP_K: int = 4
    VECTOR_SELECT_THRESHOLD: float = 0.5
    
    # minio
    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SCCRET_KEY: str = ""
    MINIO_JM_BOCKET_NAME: str = "jm-repertory"
    MINIO_RANDOM_PIC_BOCKET_NAME: str = "random-pic"


class LogSetting(BaseSettings):
    # logger
    LOG_NAME: str = "log.qqbot.record"
    LOG_PATH: str = "./log"
    LOG_FILE_LEVEL: str = "DEBUG"
    LOG_STREAM_LEVEL: str = "INFO"
    LOG_FILE_ENCODING: str = "utf-8"
    LOG_CONSOLE_OUTPUT: bool = False


class ServiceSetting(BaseSettings):
    # GPT
    GPT_BASE_URL: str = ""
    GPT_API_KEY: str = ""
    GPT_DEFAULT_MODEL: str = "gpt-3.5-turbo-ca"
    GPT_TEMPERATURE: float = 0.8
    GPT_RESPONSE_FORMAT: dict = {"type": "json_object"}
    
    # BGE_M3
    EMBEDDING_BASE_URL: str = ""
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "bge-m3"
    

class Setting(SysSetting, DBSetting, LogSetting, ServiceSetting):
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Setting()
