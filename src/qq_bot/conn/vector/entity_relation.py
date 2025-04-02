from datetime import datetime
from llama_index.core.schema import NodeWithScore
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores.types import MetadataFilters

from qq_bot.utils.models import (
    EntityObject,
    GroupMessageRecord,
    RelationTriplet,
)
from qq_bot.conn.vector.base import VectorStoreBase
from qq_bot.utils.config import settings


class EntityRelationVectorStore(VectorStoreBase):
    def __init__(self, *args, entity_store: str, relation_store: str, **kwargs):
        super().__init__(*args, stores=[entity_store, relation_store], **kwargs)

    def insert_vector_from_triplets(
        self,
        triplets: list[RelationTriplet],
    ) -> None:
        entities: set[EntityObject] = set()
        for triplet in triplets:
            entities.update([triplet.subject, triplet.object])

        relation_docs = [
            Document(
                text=triplet.relation.name,
                metadata={
                    "relation_id": triplet.relation.id,
                },
            )
            for triplet in triplets
        ]
        entity_docs = [
            Document(
                text=entity.name,
                metadata={
                    "entity_id": entity.id,
                    "attribute": entity.attribute,
                    "real_id": entity.real_id,
                },
            )
            for entity in entities
        ]
        self.insert_vector(relation_docs, "relations")
        self.insert_vector(entity_docs, "entities")


er_vector_store = EntityRelationVectorStore(
    emb_url=settings.EMBEDDING_BASE_URL,
    emb_key=settings.EMBEDDING_API_KEY,
    emb_model=settings.EMBEDDING_MODEL,
    store_url=settings.VECTOR_STORE_URL,
    store_token=settings.VECTOR_STORE_TOKEN,
    entity_store=settings.ENTITY_VECTOR_STORE_NAME,
    relation_store=settings.RELATION_VECTOR_STORE_NAME,
)
