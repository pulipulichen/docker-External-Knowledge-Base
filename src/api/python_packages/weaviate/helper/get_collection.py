
from .get_client import get_client

import weaviate
import os
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType, Tokenization

# https://weaviate.io/developers/weaviate/connections/connect-local
def get_collection(collection_name):
  client = get_client()

  if collection_name is None:
    collection_name = os.getenv('DATABASE_COLLECTION_NAME', 'knowledge_base')
  
  if client.collections.exists(collection_name):
    return client.collections.get(collection_name)

  collection = client.collections.create(
    collection_name,
    # 設置 "none" 表示不使用預設向量化器，而是使用自定義向量
    vectorizer_config=wvc.config.Configure.Vectorizer.none(),
    properties=[
        Property(
          name="_index",
          data_type=DataType.TEXT,
          vectorize_property_name=True,
          tokenization=Tokenization.WHITESPACE
        )
    ],
  )

  # print(collection)

  return collection