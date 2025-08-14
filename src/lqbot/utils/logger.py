from ncatbot.utils import get_log

logger = get_log()

# import logging
# import logging.config
# import os
# import time

# from uvicorn.config import LOGGING_CONFIG

# from lqbot.utils.config import settings


# FILE_HANDLER_NAME = "file"
# CONSOLE_HANDLER_NAME = "console"
# FORMAT = "[%(asctime)s.%(msecs)03d] %(filename)-20s -> line:%(lineno)-5d [%(levelname)s]:  %(message)s"
# LOG_COLOR_CONFIG = {
#     "DEBUG": "white",
#     "INFO": "green",
#     "WARNING": "yellow",
#     "ERROR": "red",
#     "CRITICAL": "bold_red",
# }


# def generate_filepath(filename: str, filepath: str) -> str:
#     if not os.path.isdir(filepath):
#         os.makedirs(filepath)
#     return os.path.join(filepath, filename)


# def set_handler_no_color(
#     config: dict, formatter_key: str, handlers_key: str, **kwargs
# ) -> None:
#     config["formatters"].setdefault(formatter_key, {})
#     config["handlers"].setdefault(handlers_key, {})

#     config["formatters"][formatter_key].update(
#         {
#             "format": FORMAT,
#             "datefmt": "%Y-%m-%d %H:%M:%S",
#         }
#     )
#     config["handlers"][handlers_key].update({"formatter": formatter_key, **kwargs})


# def set_handler_with_color(
#     config: dict, formatter_key: str, handlers_key: str, **kwargs
# ) -> None:
#     set_handler_no_color(config, formatter_key, handlers_key, **kwargs)
#     config["formatters"][formatter_key].update(
#         {
#             "()": "colorlog.ColoredFormatter",
#             "format": f"%(log_color)s{FORMAT}",
#             "log_colors": LOG_COLOR_CONFIG,
#         }
#     )


# def get_uvicorn_logger_config() -> dict:
#     logging_config = LOGGING_CONFIG
#     set_handler_no_color(
#         config=logging_config, formatter_key="default", handlers_key="default"
#     )
#     set_handler_no_color(
#         config=logging_config, formatter_key="access", handlers_key="access"
#     )

#     return logging_config


# def get_system_logger_config(filename: str) -> dict:
#     handlers = (
#         [FILE_HANDLER_NAME, CONSOLE_HANDLER_NAME]
#         if settings.LOG_CONSOLE_OUTPUT
#         else [FILE_HANDLER_NAME]
#     )
#     logging_config = {
#         "version": 1,
#         "disable_existing_loggers": False,
#         "formatters": {},
#         "handlers": {},
#         "loggers": {
#             settings.LOG_NAME: {
#                 "handlers": handlers,
#                 "level": "DEBUG",
#                 "propagate": True,
#             },
#         },
#     }
#     # configure logger for file
#     set_handler_no_color(
#         config=logging_config,
#         formatter_key=FILE_HANDLER_NAME,
#         handlers_key=FILE_HANDLER_NAME,
#         **{
#             "class": "logging.FileHandler",
#             "level": settings.LOG_FILE_LEVEL,
#             "mode": "a",
#             "filename": filename,
#             "encoding": settings.LOG_FILE_ENCODING,
#         },
#     )
#     # configure logger for console
#     set_handler_with_color(
#         config=logging_config,
#         formatter_key=CONSOLE_HANDLER_NAME,
#         handlers_key=CONSOLE_HANDLER_NAME,
#         **{
#             "class": "logging.StreamHandler",
#             "level": settings.LOG_STREAM_LEVEL,
#         },
#     )
#     return logging_config


# def get_logger_absolute_path(filename: str):
#     return generate_filepath(
#         filename=f'{filename}-{time.strftime("%Y-%m-%d", time.localtime())}.log',
#         filepath=os.path.join(os.getcwd(), settings.LOG_ROOT),
#     )


# def get_logger(use_default: bool = False) -> logging.Logger:
#     if use_default:
#         return logging.getLogger(settings.LOG_NAME)
#     else:
#         filename = get_logger_absolute_path(
#             filename=settings.PROJECT_NAME.replace(" ", "")
#         )
#         logging_config = get_system_logger_config(filename=filename)
#         logging.config.dictConfig(logging_config)
#         return logging.getLogger(settings.LOG_NAME)


# logger = get_logger(use_default=True)
