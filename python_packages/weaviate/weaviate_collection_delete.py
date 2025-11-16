from .helper.get_client import get_client
import os

def weaviate_collection_delete(**kwargs):

  collection_name = kwargs.get("knowledge_id", None)
  
  if collection_name is None:
    collection_name = os.getenv('DATABASE_COLLECTION_NAME', 'knowledge_base')

  client = get_client()
  if client.collections.exists(collection_name):
    return client.collections.delete(collection_name)

  return False
  