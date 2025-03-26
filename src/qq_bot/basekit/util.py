import asyncio
import functools
import inspect
import json
import os
import re

import yaml
from PIL import Image
from botpy.message import GroupMessage, Message
from qq_bot.basekit.models import GroupMessageRecord
from qq_bot.db.sql.models import GroupBotMessage
from qq_bot.basekit.logging import logger





def load_yaml(yaml_path: str) -> dict:
    try:
        with open(yaml_path) as yaml_file:
            return yaml.safe_load(yaml_file)
    except Exception as err:
        raise Exception(f"[YAML Reader] Error occured when read YAML from path '{yaml_path}'. Error: {err}") from err


def parse_text_2_json(text: str) -> dict[str, str] | None:
    text = text.replace("```json\n", "").replace("\n```", "").replace("\n", "")
    try:
        json_matches = re.compile(r"\{.*?\}").findall(text)
        for match in json_matches:
            text_json = json.loads(match)
            return text_json
    except Exception as err:
        return None


def groupchat_query_keywords_replace(
    messages: list[GroupMessageRecord],
    current_sender: str
) -> list[str]:
    """替换人称代词等，确保模型能更好地理解知识库信息

    Args:
        messages (list[GroupUserMessage]): vector db中存储的相关知识
        current_sender (str): 当前提问的用户，该变量为了辅助分辨知识库中的代词关系

    Returns:
        list[str]: _description_
    """
    def replace_pronoun(msg: GroupMessageRecord) -> GroupMessageRecord:
        # if msg.sender_id == current_sender:
        #     me_cn_subst = "提问者"
        #     us_cn_subst = "提问者与一些人"
        #     me_i_en_subst = " questioner "
        #     my_en_subst = " questioner's "
        if msg.sender_id != current_sender:
            me_cn_subst = "另外某个人"
            us_cn_subst = "另外一群人"
            me_i_en_subst = " another people "
            my_en_subst = " another people's "
        
            msg.content = re.sub(r"我们|俺们", us_cn_subst, msg.content)
            msg.content = re.sub(r"我|俺", me_cn_subst, msg.content)
            msg.content = re.sub(r" me | i ", me_i_en_subst, msg.content)
            msg.content = re.sub(r" my ", my_en_subst, msg.content)
        return msg
    def replace_pronoun(msg: GroupMessageRecord) -> GroupMessageRecord:
        # if msg.sender_id == current_sender:
        #     me_cn_subst = "提问者"
        #     us_cn_subst = "提问者与一些人"
        #     me_i_en_subst = " questioner "
        #     my_en_subst = " questioner's "
        if msg.sender_id != current_sender:
            me_cn_subst = "另外某个人"
            us_cn_subst = "另外一群人"
            me_i_en_subst = " another people "
            my_en_subst = " another people's "
        
            msg.content = re.sub(r"我们|俺们", us_cn_subst, msg.content)
            msg.content = re.sub(r"我|俺", me_cn_subst, msg.content)
            msg.content = re.sub(r" me | i ", me_i_en_subst, msg.content)
            msg.content = re.sub(r" my ", my_en_subst, msg.content)
        return msg
    
    results = [replace_pronoun(message).content for message in messages]
    return results


def encapsulated_group_chat_message(
    message: GroupMessage, 
    need_split: bool = False
) -> GroupMessageRecord | list[GroupMessageRecord]:
    if need_split:
        contents = [m for m in str(message.content).split(r'[。？！.?!]') if m]
        result = [
            GroupMessageRecord(
                id=message.id,
                content=content,
                group_id=message.group_openid,
                sender_id=message.author.member_openid,
                create_time=message.timestamp
            )
            for content in contents
        ]
    else:
        result = GroupMessageRecord(
            id=message.id,
            content=message.content,
            group_id=message.group_openid,
            sender_id=message.author.member_openid,
            create_time=message.timestamp
        )
    return result


def encapsulated_bot_group_reply(info: dict, content: str, group_id: str) -> GroupMessageRecord:
    result = GroupMessageRecord(
        id=info["id"],
        content=content,
        group_id=group_id,
        sender_id="",
        create_time=info["timestamp"]
    )
    return result


def cut_sentences_with_id(sentences: list[str]) -> str:
    result = "\n".join([f"{i}.{s}" for i, s in enumerate(sentences)])
    return result


def stitched_images(images: list[Image.Image]) -> Image.Image | None: 
    if len(images) > 0:
        width = 1024
        
        new_images = []
        for image in images:
            w, h = image.size
            new_images.append(image.resize((width, int(h * width / w)), Image.LANCZOS))
        
        
        # width, _ = images[0].size
        mode = new_images[0].mode
        height = sum(i.size[1] for i in new_images)
        
        result = Image.new(mode=mode, size=(width, height))
        
        current_height = 0
        for i, image in enumerate(new_images):
            result.paste(image, box=(0, current_height))
            current_height += image.size[1]
        return result


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