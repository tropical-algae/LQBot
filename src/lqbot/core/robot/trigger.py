import os
import random
from datetime import datetime

from ncatbot.core import BotAPI, BotClient, GroupMessage, PrivateMessage
from PIL import Image

from lqbot.core.robot.handlers.command import command_runner
from lqbot.core.robot.handlers.sender import group_chat, send_group_message
from lqbot.utils.config import settings
from lqbot.utils.decorator import MessageCommands
from lqbot.utils.logger import logger
from lqbot.utils.models import GroupMessageData
from lqbot.utils.util import blue_image, text_simplification

# @MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_RANDOM_PIC}")
# async def group_random_picture(
#     agent: AgentBase, message: GroupMessageData, **kwargs
# ) -> bool:
#     logger.info(f"[{message.id}] 随机图片命令触发")

#     local_file, url = wallpaper_provider.load()
#     if local_file:
#         remote_file = os.path.join(
#             datetime.now().strftime("%Y-%m"), os.path.basename(local_file)
#         )
#         minio.upload_files(
#             bucket=settings.MINIO_WALLPAPER_BOCKET_NAME,
#             upload_file={local_file: remote_file},
#         )

#         await agent.api.post_group_msg(message.group_id, image=url)
#         os.remove(local_file)
#     return True


# @MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_RANDOM_SETU}")
# async def group_random_setu(
#     agent: AgentBase, message: GroupMessageData, **kwargs
# ) -> bool:
#     logger.info(f"[{message.id}] 随机setu命令触发")

#     num = 1

#     logger.info(f"[SETU]: GROUP {message.group_id} -> 准备发送{num}张")
#     for local_file_origin, url in wallpaper_provider.load_r18(num=num):
#         if local_file_origin and url:
#             local_time = datetime.now().strftime("%Y-%m")
#             remote_file_origin = os.path.join(
#                 local_time, "origin", os.path.basename(local_file_origin)
#             )

#             local_file_processed = f"{'.'.join(local_file_origin.split('.')[:-1])}_processed.{local_file_origin.split('.')[-1]}"

#             blue_image(Image.open(local_file_origin)).save(local_file_processed)

#             minio.upload_files(
#                 bucket=settings.MINIO_WALLPAPER_BOCKET_NAME,
#                 upload_file={local_file_origin: remote_file_origin},
#             )
#             bastion_message = await agent.api.post_group_msg(
#                 group_id=message.group_id, image=local_file_processed
#             )

#             if bastion_message["status"] == "ok":
#                 logger.info(
#                     f"[SETU]: GROUP {message.group_id} -> {local_file_origin} 已发送"
#                 )
#             else:
#                 logger.warning(
#                     f"[SETU]: GROUP {message.group_id} -> {local_file_origin} 发送失败"
#                 )

#             os.remove(local_file_origin)
#             os.remove(local_file_processed)

#     return True


# @MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_TOOL}", need_at=True)
# async def group_use_tool(agent: AgentBase, message: GroupMessageData, **kwargs) -> bool:
#     status = await tool_component.run(agent=agent, message=message)
#     if status:
#         logger.info(f"[{message.id}] 工具调用触发")

#     return status


@MessageCommands(command="", need_at=True)
async def group_at_trigger(api: BotAPI, message: GroupMessageData, **_) -> bool:
    logger.info(f"[GROUP {message.group_id}] 触发AT聊天")
    status = await group_chat(api=api, message=message)
    return status


@MessageCommands(command=settings.BOT_COMMAND_GROUP_CHAT)
async def group_chat_trigger(api: BotAPI, message: GroupMessageData, **_) -> bool:
    logger.info(f"[GROUP {message.group_id}] 触发指名聊天")
    status = await group_chat(api=api, message=message)
    return status


@MessageCommands(command=settings.BOT_COMMAND_GROUP_COMMAND)
async def group_command_trigger(
    api: BotAPI, message: GroupMessageData, params: str, **_
) -> bool:
    logger.info(f"[GROUP {message.group_id}] 触发指令 -> {params}")
    try:
        result = command_runner.execute_command(params)
        result = text_simplification(result, 1000)
        await send_group_message(api=api, group_id=message.group_id, text=result)
        return True
    except Exception as err:
        logger.error(f"[GROUP {message.group_id}] 指令执行失败 {params} -> {err}")
        return False
