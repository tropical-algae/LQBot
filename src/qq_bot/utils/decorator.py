import asyncio
import functools
import inspect
from typing import Callable
from ncatbot.core.message import BaseMessage, GroupMessage, PrivateMessage
from qq_bot.conn.sql.session import LocalSession

from qq_bot.utils.logging import logger
from qq_bot.utils.util_text import get_data_from_message


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
            max_times = getattr(args[0], 'times', 3) if is_method else (times or 3)
            
            self = args[0] if is_method else None
            func_path = f"{type(self).__name__ + '.' if self else ''}{func.__name__}"
            

            for attempt in range(1, max_times + 1):
                result = await func(*args, **kwargs)
                if result is not None:
                    return result
                logger.warning(f"RETRY[{attempt}/{max_times}]: function -> {func_path}")
            logger.warning(f"RETRY CAN NOT FIX ERROR: function -> {func_path}")
            return None

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            is_method = len(args) > 0 and inspect.isclass(type(args[0]))
            max_times = getattr(args[0], 'times', 3) if is_method else (times or 3)
            
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
            if isinstance(origin_msg, GroupMessage):
                content: str = get_data_from_message(origin_msg.message, "text").get("text", "").strip()
                at: bool = (
                    True if not self.need_at else 
                    (str(get_data_from_message(origin_msg.message, "at").get("qq", "-1")) == str(origin_msg.self_id))
                )
            elif isinstance(origin_msg, PrivateMessage):
                content: str = get_data_from_message(origin_msg.message, "text").get("text", "").strip()
                at: bool = True

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
    """agent工具的日志装饰器
    """
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
