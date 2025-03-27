import base64
from datetime import datetime
import os
import random
from botpy.ext.command_util import Commands
from botpy import BotAPI
from botpy.message import GroupMessage, Message

from PIL import Image
import requests
from qq_bot.basekit.logging import logger
from qq_bot.basekit.models import GroupMessageRecord
from qq_bot.basekit.util import cut_sentences_with_id, encapsulated_bot_group_reply, encapsulated_group_chat_message, groupchat_query_keywords_replace, stitched_images
from qq_bot.db.sql.crud.ofcl_group_message_crud import insert_bot_group_message, insert_query_reocrd_relation, insert_user_group_message
from qq_bot.db.vector.base import build_filter
from qq_bot.db.vector.crud import insert_text_embedding, select_text_embedding
from qq_bot.basekit.config import settings
from qq_bot.service.chat_gpt.vector_query import vector_query_gpt
from qq_bot.service.resource_loader.jm_capturer import jm
from qq_bot.service.resource_loader.random_pic_capturer import random_pic
from qq_bot.db.minio.base import minio

from qq_bot.db.sql.session import LocalSession


@Commands(f"{settings.BOT_COMMAND_GROUP_QUERY}")
async def group_select(api: BotAPI, message: GroupMessage, params=None):
    message.content = params
    user_msg_id = message.id
    group_id = message.group_openid
    user_id = message.author.member_openid

    # 语义理解，从历史记录找出相关的信息
    logger.info(f"User[{user_id}] group_query: {params}")
    filter = build_filter(condition={"group_id": message.group_openid})
    knowlgs: list[GroupMessageRecord] = await select_text_embedding(
        text=params,
        top_k=settings.VECTOR_SELECT_TOP_K,
        threshold=settings.VECTOR_SELECT_THRESHOLD,
        filter=filter
    )
    knowlg_len = len(knowlgs)
    valid_knowlg_indexs = {}
    if len(knowlgs) > 0:
        # 筛选能回答问题的信息组件知识库
        knowlg_texts = groupchat_query_keywords_replace(knowlgs, user_id)
        information = cut_sentences_with_id(knowlg_texts)
        valid_knowlg_indexs = await vector_query_gpt.capture_relation_knowledge(
            input={"question": params, "information": information}
        )
        # 依据知识库生成问题回复
        if len(valid_knowlg_indexs) > 0:
            valid_knowlg_texts = [knowlg_texts[i] for i in valid_knowlg_indexs.keys() if 0 <= i < knowlg_len]
            information = cut_sentences_with_id(valid_knowlg_texts)
            reply = await vector_query_gpt.run(
                input={ "question": params, "information": information}
            )
        else:
            reply = "不知道怎么回答你哦～"
    else:
        reply = "好像回答不了你的问题呢～"
    # 回答用户问题
    reply_result = await api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0, 
        msg_id=message.id,
        content=reply
    )
    # 存储数据库
    with LocalSession() as db:
        msg_type = settings.DB_GROUP_TYPE_MAPPING[settings.BOT_COMMAND_GROUP_QUERY]
        user_msg = encapsulated_group_chat_message(message)
        bot_msg = encapsulated_bot_group_reply(reply_result, reply, group_id)
        record_ids = [
            knowlgs[i].id for i in valid_knowlg_indexs.keys() if 0 <= i < knowlg_len
        ]
        record_scores = [
            score for i, score in valid_knowlg_indexs.items()
            if 0 <= i < knowlg_len
        ]
        insert_user_group_message(db=db, message=user_msg, type=msg_type)
        insert_bot_group_message(db=db, user_msg_id=user_msg_id, message=bot_msg)
        insert_query_reocrd_relation(db=db, query_id=user_msg.id, record_ids=record_ids, scores=record_scores)
    return True


@Commands(f"{settings.BOT_COMMAND_GROUP_RECORD}")
async def group_insert(api: BotAPI, message: GroupMessage, params=None):
    logger.info(f"User[{message.author.member_openid}] group_insert: {params}")
    message.content = params
    group_message = encapsulated_group_chat_message(message=message)

    reply = "收到了喵～"
    await api.post_group_message(
        group_openid=message.group_openid,
        msg_type=0,
        msg_id=message.id,
        content=reply
    )
    insert_text_embedding(messages=[group_message])
    with LocalSession() as db:
        msg_type = settings.DB_GROUP_TYPE_MAPPING[settings.BOT_COMMAND_GROUP_RECORD]
        user_msg = encapsulated_group_chat_message(message)
        insert_user_group_message(db=db, message=user_msg, type=msg_type)

    return True


@Commands(f"{settings.BOT_COMMAND_GROUP_RANDOM_PIC}")
async def group_jm_pic(api: BotAPI, message: GroupMessage, params=None):
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

        uploadMedia = await api.post_group_file(
            group_openid=message.group_openid, 
            file_type=1,
            url=url
        )
        await message._api.post_group_message(
            group_openid=message.group_openid,
            msg_type=7,
            msg_id=message.id,
            media=uploadMedia
        )
        os.remove(local_file)
    return True


# @Commands(f"{settings.BOT_COMMAND_GROUP_JM_CHECK}")
# async def group_jm_pic(api: BotAPI, message: GroupMessage, params=None):
    
#     # file_url = "http://175.178.43.109:10002/1034997/1/00001.jpg"  # 这里需要填写上传的资源Url
#     msg_seq = 0
    
#     try:
#         jm_id = int(params)
#         reply_content = "收到啦~正在努力寻找喵~"
#     except Exception as err:
#         reply_content = "看不懂的编号喵~"
#         logger.warning(f"{err}. Invalid jm id: {params}")
#     finally:
#         # await api.post_group_message(
#         #     group_openid=message.group_openid,
#         #     msg_type=0,
#         #     msg_id=message.id,
#         #     msg_seq=0,
#         #     content=reply_content
#         # )
#         msg_seq += 1
    
#     local_roots: list[str] = jm.download(jm_id)
    
#     for local_root in local_roots:
#         image_names = sorted(
#             [i for i in os.listdir(local_root) if i.endswith('.jpg')],
#             key=lambda x: int(x.split(".")[0])
#         )
#         image_files = [os.path.join(local_root, i) for i in image_names]
#         images = [Image.open(i) for i in image_files ]
        
#         processed_image_file = f"{local_root}.jpg"
#         processed_image_bocket_path = os.path.join(
#             params, 
#             os.path.basename(processed_image_file)
#         )
#         # processed_image = stitched_images(images=images)
#         # processed_image.save(processed_image_file)
        
#         # minio.upload_files(
#         #     bucket=settings.MINIO_JM_BOCKET_NAME,
#         #     upload_file={processed_image_file: processed_image_bocket_path}
#         # )
#         minio.upload_files(
#             bucket=settings.MINIO_JM_BOCKET_NAME,
#             upload_file={i: "/".join(i.split("/")[-3:]) for i in image_files}
#         )
        
#         file_url = minio.get_file_url(
#             bucket=settings.MINIO_JM_BOCKET_NAME,
#             object_path="/".join(image_files[0].split("/")[-3:]) # processed_image_bocket_path
#         )
#         await message._api.post_group_message(
#             group_openid=message.group_openid,
#             msg_type=0,  # 7表示富媒体类型
#             msg_id=message.id, 
#             msg_seq=msg_seq,
#             content=file_url
#         )

#         # uploadMedia = await api.post_group_file(
#         #     group_openid=message.group_openid, 
#         #     file_type=1, # 文件类型要对应上，具体支持的类型见方法说明
#         #     url=file_url # 文件Url
#         # )

#         # # 资源上传后，会得到Media，用于发送消息
#         # await message._api.post_group_message(
#         #     group_openid=message.group_openid,
#         #     msg_type=7,  # 7表示富媒体类型
#         #     msg_id=message.id, 
#         #     msg_seq=msg_seq,
#         #     media=uploadMedia
#         # )
#         msg_seq += 1
#     return True
