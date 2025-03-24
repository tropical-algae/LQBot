from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.vector_stores.types import MetadataFilters, MetadataFilter
from qq_bot.common.config import settings


embed_model = OpenAIEmbedding(
    api_base=settings.EMBEDDING_BASE_URL,
    api_key=settings.EMBEDDING_API_KEY,
    model_name=settings.EMBEDDING_MODEL,
    embed_batch_size=10,
    num_workers=6,
)

vector_store = MilvusVectorStore(
    uri=settings.VECTOR_STORE_URL,
    token=settings.VECTOR_STORE_TOKEN,
    collection_name=settings.VECTOR_STORE_NAME,
    # overwrite=True,
    dim=1024,
)

storage_context = StorageContext.from_defaults(vector_store=vector_store)

vector_store: VectorStoreIndex = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    embed_model=embed_model,
)


def build_filter(condition: dict):
    filter = MetadataFilters(
        filters=[
            MetadataFilter(
                key=key,
                value=value
            )
            for key, value in condition.items()
        ]
    )
    return filter
