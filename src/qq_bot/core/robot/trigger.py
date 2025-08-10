import os
from datetime import datetime
import random
from ncatbot.core import BotAPI, BotClient, GroupMessage, PrivateMessage
from PIL import Image

from qq_bot.core.robot.base import AgentBase
from qq_bot.utils.decorator import MessageCommands
from qq_bot.utils.models import GroupMessageRecord
from qq_bot.utils.util import blue_image
from qq_bot.core.robot.service import group_chat, send_message
from qq_bot.core import wallpaper_provider
from qq_bot.core.components.toolbox import tool_component
from qq_bot.conn.minio.base import minio
from qq_bot.utils.config import settings
from qq_bot.utils.logger import logger
from qq_bot.core.components.command import command_runner
from qq_bot.utils.util_text import text_simplification

@MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_RANDOM_PIC}")
async def group_random_picture(
    agent: AgentBase, message: GroupMessageRecord, **kwargs
) -> bool:
    logger.info(f"[{message.id}] 随机图片命令触发")

    local_file, url = wallpaper_provider.load()
    if local_file:
        remote_file = os.path.join(
            datetime.now().strftime("%Y-%m"), os.path.basename(local_file)
        )
        minio.upload_files(
            bucket=settings.MINIO_WALLPAPER_BOCKET_NAME,
            upload_file={local_file: remote_file},
        )

        await agent.api.post_group_msg(message.group_id, image=url)
        os.remove(local_file)
    return True


@MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_RANDOM_SETU}")
async def group_random_setu(
    agent: AgentBase, message: GroupMessageRecord, **kwargs
) -> bool:
    logger.info(f"[{message.id}] 随机setu命令触发")

    num = 1

    logger.info(f"[SETU]: GROUP {message.group_id} -> 准备发送{num}张")
    for local_file_origin, url in wallpaper_provider.load_r18(num=num):
        if local_file_origin and url:
            local_time = datetime.now().strftime("%Y-%m")
            remote_file_origin = os.path.join(
                local_time, "origin", os.path.basename(local_file_origin)
            )

            local_file_processed = f"{'.'.join(local_file_origin.split('.')[:-1])}_processed.{local_file_origin.split('.')[-1]}"

            blue_image(Image.open(local_file_origin)).save(local_file_processed)

            minio.upload_files(
                bucket=settings.MINIO_WALLPAPER_BOCKET_NAME,
                upload_file={local_file_origin: remote_file_origin},
            )
            bastion_message = await agent.api.post_group_msg(
                group_id=message.group_id, image=local_file_processed
            )

            if bastion_message["status"] == "ok":
                logger.info(
                    f"[SETU]: GROUP {message.group_id} -> {local_file_origin} 已发送"
                )
            else:
                logger.warning(
                    f"[SETU]: GROUP {message.group_id} -> {local_file_origin} 发送失败"
                )

            os.remove(local_file_origin)
            os.remove(local_file_processed)

    return True


@MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_TOOL}", need_at=True)
async def group_use_tool(agent: AgentBase, message: GroupMessageRecord, **kwargs) -> bool:
    status = await tool_component.run(agent=agent, message=message)
    if status:
        logger.info(f"[{message.id}] 工具调用触发")

    return status


@MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_REPLY}", need_at=True)
async def group_at_reply(agent: AgentBase, message: GroupMessageRecord, **kwargs) -> bool:
    use_voice: bool = random.random() < settings.VOICE_WILLINGNESS
    status = await group_chat(api=agent.api, message=message, split=True, voice=use_voice)
    if status:
        logger.info(f"[{message.id}] AT回复触发")
    return status


@MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_CHAT}")
async def group_at_chat(agent: AgentBase, message: GroupMessageRecord, **kwargs) -> bool:
    can_chat: bool = random.random() < settings.CHAT_WILLINGNESS
    use_voice: bool = random.random() < settings.VOICE_WILLINGNESS
    if can_chat:
        status = await group_chat(api=agent.api, message=message, split=True, voice=use_voice)
        if status:
            logger.info(f"[{message.id}] 随机聊天触发")
        return status
    return False


@MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_COMMAND}")
async def group_command(agent: AgentBase, message: GroupMessageRecord, params: str, **kwargs) -> bool:
    result = command_runner.execute_command(params)
    result = text_simplification(result, 1000)
    status = await send_message(api=agent.api, group_id=message.group_id, text=result, voice=False)
    # status = await group_chat(api=agent.api, message=message, split=False, voice=False)
    if status:
        logger.info(f"[{message.id}] 指令触发: {params}")
    return status
