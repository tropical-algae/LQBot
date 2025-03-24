from datetime import datetime
from llama_index.core.schema import NodeWithScore
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores.types import MetadataFilters

from qq_bot.common.models import GroupMessageRecord
from qq_bot.db.vector.base import storage_context, embed_model, vector_store

def insert_text_embedding(messages: list[GroupMessageRecord] | GroupMessageRecord):
    if isinstance(messages, GroupMessageRecord):
        messages = [messages]
    
    documents = [
        Document(
            text=message.content,
            metadata={
                "id": message.id,
                "group_id": message.group_id,
                "sender_id": message.sender_id,
                "time": message.create_time
            },
        )
        for message in messages
    ]

    VectorStoreIndex.from_documents(
        documents=documents,
        storage_context=storage_context,
        embed_model=embed_model,
        insert_batch_size=100,
        show_progress=True,
        transformations=[SentenceSplitter(chunk_size=2048)],
    )


async def select_text_embedding(
    text: str, 
    top_k: int = 5, 
    threshold: float = 0.5,
    filter: MetadataFilters | None = None
) -> list[GroupMessageRecord]:
    params = {"similarity_top_k": top_k}
    if filter:
        params["filters"] = filter

    retriever = vector_store.as_retriever(**params)
    target_data: list[NodeWithScore] = await retriever.aretrieve(text)
    result = [
        GroupMessageRecord(
            id=data.metadata["id"],
            content=data.text,
            group_id=data.metadata["group_id"],
            sender_id=data.metadata["sender_id"],
            create_time=data.metadata["time"]
        )
        for data in target_data if data.score > threshold
    ]
    return result
