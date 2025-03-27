import asyncio
import functools
import inspect
from ncatbot.core.message import BaseMessage, GroupMessage, PrivateMessage

from qq_bot.basekit.logging import logger
from qq_bot.basekit.util import get_data_from_message


def function_retry(times=None):
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
        async def decorated(*args, **kwargs):
            message: BaseMessage = kwargs["message"]
            if isinstance(message, GroupMessage):
                content: str = get_data_from_message(message.message, "text").get("text", "").strip()
                at: bool = (
                    True if not self.need_at else 
                    (str(get_data_from_message(message.message, "at").get("qq", "-1")) == str(message.self_id))
                )
            elif isinstance(message, PrivateMessage):
                content: str = get_data_from_message(message.message, "text").get("text", "").strip()
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

        return decorated