
from .get_client import get_client

import weaviate
import os
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType, Tokenization


# https://weaviate.io/developers/weaviate/connections/connect-local
def is_collection_existed(collection_name):
  client = get_client()

  if collection_name is None:
    collection_name = os.getenv('DATABASE_COLLECTION_NAME', 'knowledge_base')
  
  try:
    return client.collections.exists(collection_name)
  except Exception as e:
    return False
