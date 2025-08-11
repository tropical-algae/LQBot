import asyncio
import functools
import inspect
from typing import Any, Callable
from ncatbot.core.message import BaseMessage, GroupMessage, PrivateMessage
from qq_bot.conn.sql.session import LocalSession

from qq_bot.utils.logger import logger
from qq_bot.utils.config import settings
from qq_bot.utils.util import get_data_from_message


PRINTABLE_TYPES = (int, float, str, bool, list, dict, tuple, type(None))


def function_retry(times=None):
    """重试装饰器，兼容函数、类函数、同步/异步函数

    Args:
        times (_type_, optional): 重试次数. Defaults to None.
    """

    def decorator(func):
        is_coroutine = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            is_method = len(args) > 0 and inspect.isclass(type(args[0]))
            max_times = getattr(args[0], "times", 3) if is_method else (times or 3)

            self = args[0] if is_method else None
            func_path = f"{type(self).__name__ + '.' if self else ''}{func.__name__}"

            for attempt in range(1, max_times + 1):
                result = await func(*args, **kwargs)
                if result is not None:
                    return result
                logger.warning(f"重试[{attempt}/{max_times}]: function -> {func_path}")
            logger.warning(f"重试未能解决问题: function -> {func_path}")
            return None

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            is_method = len(args) > 0 and inspect.isclass(type(args[0]))
            max_times = getattr(args[0], "times", 3) if is_method else (times or 3)

            self = args[0] if is_method else None
            func_path = f"{type(self).__name__ + '.' if self else ''}{func.__name__}"

            for attempt in range(1, max_times + 1):
                result = func(*args, **kwargs)
                if result is not None:
                    return result
                logger.warning(f"RETRY[{attempt}/{max_times}]: function -> {func_path}")
            logger.warning(f"RETRY CAN NOT FIX ERROR: function -> {func_path}")
            return None

        return async_wrapper if is_coroutine else sync_wrapper

    if callable(times):
        func = times
        times = None
        return decorator(func)

    return decorator


class MessageCommands:
    """
    指令装饰器

    Args:
      args (tuple): 字符串元组。
    """

    def __init__(self, command: list | str, need_at: bool = False):
        self.commands = command if isinstance(command, list) else [command]
        self.need_at = need_at

    def __call__(self, func):
        @functools.wraps(func)
        async def decorator(*args, **kwargs):
            origin_msg: BaseMessage = kwargs["origin_msg"]

            # 处理群聊指令
            if isinstance(origin_msg, GroupMessage):
                func_name = func.__name__
                white_list = settings.GROUP_INSTRUCT_WHITE.get(func_name, [])
                black_list = settings.GROUP_INSTRUCT_BLACK.get(func_name, [])

                # 检测黑白名单
                if white_list:
                    if origin_msg.group_id not in white_list:
                        logger.warning(
                            f"GROUP [{origin_msg.group_id}] 未添加功能白名单：{func_name}"
                        )
                        return False
                elif origin_msg.group_id in black_list:
                    logger.warning(
                        f"GROUP [{origin_msg.group_id}] 功能被拉黑：{func_name}"
                    )
                    return False

                content: str = (
                    get_data_from_message(origin_msg.message, "text")
                    .get("text", "")
                    .strip()
                )
                at: bool = (
                    True
                    if not self.need_at
                    else (
                        str(
                            get_data_from_message(origin_msg.message, "at").get(
                                "qq", "-1"
                            )
                        )
                        == str(origin_msg.self_id)
                    )
                )

            # 处理私聊指令
            elif isinstance(origin_msg, PrivateMessage):
                content: str = (
                    get_data_from_message(origin_msg.message, "text")
                    .get("text", "")
                    .strip()
                )
                at: bool = True

            # 判断🐟执行
            for command in self.commands:
                is_matched: bool = True if command == "" else content.startswith(command)
                if is_matched and at:
                    # 分割指令后面的指令参数
                    params = "" if command == "" else content.split(command)[1].strip()
                    kwargs["content"] = content
                    kwargs["params"] = params
                    return await func(*args, **kwargs)
            return False

        return decorator


def tools_logger(cls):
    """agent工具的日志装饰器"""
    tool_function = cls.function

    @functools.wraps(tool_function)
    def wrapped_function(*args, **kwargs):
        param = {k: v for k, v in kwargs.items() if isinstance(v, PRINTABLE_TYPES)}
        status = tool_function(*args, **kwargs)
        if status:
            logger.info(f"工具调用成功[{cls.tool_name}]: {str(param)}")
        else:
            logger.error(f"工具调用失败[{cls.tool_name}]: {str(param)}")

        return status

    cls.function = staticmethod(wrapped_function)
    return cls


def sql_session(func: Callable):
    """SQL连接装饰器，兼容同步和异步方法

    Args:
        func (Callable):

    Returns:
        _type_:
    """
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with LocalSession() as db:
                kwargs["db"] = db
                return await func(*args, **kwargs)

        return async_wrapper  # type: ignore
    else:

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with LocalSession() as db:
                return func(*args, db=db, **kwargs)

        return sync_wrapper


def require_active(method: Callable = None, *, forcible: bool = False):
    """Decorator to check if self.active is True, unless forcible=True. Supports sync and async methods."""

    def decorator(func: Callable):
        is_async = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs) -> Any:
            active = getattr(self, "active", True)
            component = getattr(self, "__component_name__", None) or func.__name__
            if active:
                return await func(self, *args, **kwargs)
            if forcible:
                raise RuntimeError(f"Function {component} not activated")
            return None

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs) -> Any:
            active = getattr(self, "active", True)
            component = getattr(self, "__component_name__", None) or func.__name__
            if active:
                return func(self, *args, **kwargs)
            if forcible:
                raise RuntimeError(f"Function {component} not activated")
            return None

        return async_wrapper if is_async else sync_wrapper

    # Support @require_active or @require_active(forcible=True)
    if method is not None and callable(method):
        return decorator(method)
    return decorator

# def require_active(method: Callable = None, *, forcible: bool = False):
#     """Decorator to check if self.active is True, unless forcible=True"""
    
#     def decorator(func: Callable):
#         @functools.wraps(func)
#         def wrapper(self, *args, **kwargs) -> Any:
#             active = getattr(self, "active", True)
#             component = getattr(self, "__component_name__", None) or func.__name__
#             if active:
#                 return func(self, *args, **kwargs)
#             if forcible:
#                 raise RuntimeError(f"Function {component} not activated")
#             return None

#         return wrapper

#     # Detect if used as @require_active or @require_active()
#     if method is not None and callable(method):
#         return decorator(method)  # used as @require_active
#     return decorator  # used as @require_active(forcible=True)
