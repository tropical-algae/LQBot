import json
import os
import re

import yaml
from fastapi import HTTPException
from botpy.message import GroupMessage, Message
from qq_bot.common.models import GroupMessageRecord
from qq_bot.db.sql.models import GroupBotMessage


def generate_filepath(filename: str, filepath: str) -> str:
    if not os.path.isdir(filepath):
        os.makedirs(filepath)
    return os.path.join(filepath, filename)


def load_yaml(yaml_path: str) -> dict:
    try:
        with open(yaml_path) as yaml_file:
            return yaml.safe_load(yaml_file)
    except Exception as err:
        raise Exception(f"[YAML Reader] Error occured when read YAML from path '{yaml_path}'. Error: {err}") from err


def parse_text_2_json(text: str) -> tuple[dict[str, str], str]:
    text = text.replace("```json\n", "").replace("\n```", "").replace("\n", "")
    try:
        json_matches = re.compile(r"\{.*?\}").findall(text)
        for match in json_matches:
            text_json = json.loads(match)
            return text_json, "Successly parse text to json."
        raise HTTPException(status_code=500, detail="Exception: Can not parse text to json.")
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Exception: {err}") from err


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