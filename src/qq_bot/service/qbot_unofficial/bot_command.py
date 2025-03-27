import os
from datetime import datetime
from ncatbot.core import BotAPI, BotClient, GroupMessage, PrivateMessage
from PIL import Image

from qq_bot.basekit.decorator import MessageCommands
from qq_bot.basekit.util import blue_image
from qq_bot.service.qbot_unofficial.bot_server import group_random_chat
from qq_bot.service.resource_loader.random_pic_capturer import random_pic
from qq_bot.db.minio.base import minio
from qq_bot.basekit.config import settings
from qq_bot.basekit.logging import logger



@MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_RANDOM_PIC}")
async def group_random_picture(
    api: BotAPI, 
    message: GroupMessage, 
    content: str | None = None,
    params: str | None = None
) -> bool:
    
    local_file, url = random_pic.load()
    if local_file:
        remote_file = os.path.join(
            datetime.now().strftime('%Y-%m'), 
            os.path.basename(local_file)
        )
        minio.upload_files(
            bucket=settings.MINIO_RANDOM_PIC_BOCKET_NAME,
            upload_file={local_file: remote_file}
        )

        await message.api.post_group_msg(message.group_id, image=url)
        os.remove(local_file)
    return True

@MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_RANDOM_SETU}")
async def group_random_setu(
    api: BotAPI, 
    message: GroupMessage, 
    content: str | None = None,
    params: str | None = None
) -> bool:
    if message.group_id in settings.BLACK_GROUP_SETU:
        logger.warning(f"[SETU]: 被拉黑的 GROUP{message.group_id}，跳过本次处理")
        return False

    num = 1
    bastion_messages: list[int] = []
    logger.info(f"[SETU]: GROUP {message.group_id} -> 准备发送{num}张")
    for local_file_origin, url in random_pic.load_r18(num=num):
        if local_file_origin and url:
            local_time = datetime.now().strftime('%Y-%m')
            remote_file_origin = os.path.join(local_time, "origin", os.path.basename(local_file_origin))
            # remote_file_processed = os.path.join(local_time, "processed", os.path.basename(local_file_origin))

            local_file_processed = f"{'.'.join(local_file_origin.split('.')[:-1])}_processed.{local_file_origin.split('.')[-1]}"

            blue_image(Image.open(local_file_origin)).save(local_file_processed)
            
            minio.upload_files(
                bucket=settings.MINIO_RANDOM_PIC_BOCKET_NAME,
                upload_file={local_file_origin: remote_file_origin}
            )

            # bastion_message = await message.api.post_group_msg(group_id=int(settings.BASTION_GROUP), image=local_file_processed)
            bastion_message = await message.api.post_group_msg(group_id=message.group_id, image=local_file_processed)
            
            if bastion_message["status"] == "ok":
                logger.info(f"[SETU]: GROUP {message.group_id} -> {local_file_origin} 已发送")
            else:
                logger.warning(f"[SETU]: GROUP {message.group_id} -> {local_file_origin} 发送失败")

                # bastion_messages.append(bastion_message["data"]["message_id"])

            os.remove(local_file_origin)
            os.remove(local_file_processed)
    # await api.send_group_forward_msg(group_id=message.group_id, messages=bastion_messages)

    return True


@MessageCommands(command=f"{settings.BOT_COMMAND_GROUP_CHAT}", need_at=True)
async def group_at_chat(
    api: BotAPI, 
    message: GroupMessage, 
    content: str | None = None,
    params: str | None = None
) -> bool:
    return await group_random_chat(api=api, message=message, prob=1.0)
