from llama_cloud import SentenceSplitter
from llama_index.core.schema import NodeWithScore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core import StorageContext, VectorStoreIndex, Document
from llama_index.core.vector_stores.types import MetadataFilters, MetadataFilter
from qq_bot.utils.config import settings


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


class VectorStoreBase:
    def __init__(
        self, 
        emb_url: str, 
        emb_key: str, 
        emb_model: str,
        store_url: str,
        store_token: str,
        store_names: str
    ) -> None:
        vector_stores = {
            store_name: MilvusVectorStore(
                uri=store_url,
                token=store_token,
                collection_name=store_name,
                # overwrite=True,
                dim=1024,
            )
            for store_name in store_names
        }

        self.embed_model = OpenAIEmbedding(
            api_base=emb_url,
            api_key=emb_key,
            model_name=emb_model,
            embed_batch_size=10,
            num_workers=6,
        )
        self.storage_context = {
            name: StorageContext.from_defaults(vector_store=vector_store)
            for name, vector_store in vector_stores.items()
        }
        self.vector_store: dict[str, VectorStoreIndex] = {
            name: VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=self.embed_model,
            )
            for name, vector_store in vector_stores.items()
        }

    def insert_vector(self, documents: list[Document], store_name: str) -> None:
        VectorStoreIndex.from_documents(
            documents=documents,
            storage_context=self.storage_context[store_name],
            embed_model=self.embed_model,
            insert_batch_size=100,
            show_progress=True,
            transformations=[SentenceSplitter(chunk_size=2048)],
        )
    
    async def select_related_embedding(
        self,
        text: str, 
        store_name: str,
        top_k: int = 5, 
        threshold: float = 0.5,
        filter: MetadataFilters | None = None
    ) -> list:
        params = {"similarity_top_k": top_k}
        if filter:
            params["filters"] = filter

        retriever = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store[store_name],
            embed_model=self.embed_model,
        ).as_retriever(**params)
        
        result: list[NodeWithScore] = await retriever.aretrieve(text)
        
        return [data for data in result if data.score > threshold]


    
    

vector_store = VectorStoreBase(
    emb_url=settings.EMBEDDING_BASE_URL,
    emb_key=settings.EMBEDDING_API_KEY,
    emb_model=settings.EMBEDDING_MODEL,
    store_url=settings.VECTOR_STORE_URL,
    store_token=settings.VECTOR_STORE_TOKEN,
    store_names=["relations", "entities"],
)