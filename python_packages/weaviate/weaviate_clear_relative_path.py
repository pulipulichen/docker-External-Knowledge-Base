from .helper.get_collection import get_collection
from .helper.metadata_to_filters import metadata_to_filters
from .helper.get_client import get_client
from .weaviate_add import weaviate_add
import weaviate.classes as wvc

from flask import Flask
app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

import os

def weaviate_clear_relative_path(**kwargs):

  collection_name = kwargs.get("knowledge_id", None)

  if collection_name is None:
    collection_name = os.getenv('DATABASE_COLLECTION_NAME', 'knowledge_base') 
  # weaviate_collection_delete(collection_name=collection_name)
  
  relative_path = kwargs.get("relative_path")

  app.logger.info(f"relative_path: {relative_path}")

  # print({"query": item_id, "collection_name": collection_name})

  if relative_path == None:
    return False
    
  
  filters = metadata_to_filters({
    "path": relative_path
  })

  # =================================================================

  collection = get_collection(collection_name)
  
  # print({"filters": filters})

  try:
    # print("get", collection.data.get(
    #   where=filters
    # ))

    return collection.data.delete_many(
      where=filters
    )
  except Exception as e:
    # print(f"Error deleting item: {e}")
    return False

if __name__ == "__main__":
  # This is a test usage example.
  test_knowledge_id = "test_knowledge_base_item_delete"
  test_item_id_to_delete = "doc1"
  test_item_id_to_keep = "doc2"

  client = get_client()
  # Ensure the collection exists and has data
  if client.collections.exists(test_knowledge_id):
    client.collections.delete(test_knowledge_id)
    print(f"Cleaned up existing collection: {test_knowledge_id}")

  client.collections.create(
    name=test_knowledge_id,
    vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(),
    generative_config=wvc.config.Configure.Generative.openai(),
  )
  print(f"Collection '{test_knowledge_id}' created.")

  test_data_rows = [
    {
      "chunk_id": "doc1_chunk1",
      "document": "This is the first part of document one.",
      "vector": [0.1, 0.2, 0.3],
      "metadata": {"source": "doc1.txt", "page": 1, "_item_id": test_item_id_to_delete}
    },
    {
      "chunk_id": "doc1_chunk2",
      "document": "This is the second part of document one.",
      "vector": [0.4, 0.5, 0.6],
      "metadata": {"source": "doc1.txt", "page": 2, "_item_id": test_item_id_to_delete}
    },
    {
      "chunk_id": "doc2_chunk1",
      "document": "This is the only part of document two.",
      "vector": [0.7, 0.8, 0.9],
      "metadata": {"source": "doc2.txt", "page": 1, "_item_id": test_item_id_to_keep}
    },
  ]
  weaviate_add(knowledge_id=test_knowledge_id, data_rows=test_data_rows)
  print(f"Added test data to '{test_knowledge_id}'.")

  # Verify initial state
  collection = client.collections.get(test_knowledge_id)
  initial_count = collection.aggregate.over_all(total_count=True).total_count
  print(f"Initial object count in '{test_knowledge_id}': {initial_count}")

  print(f"Attempting to delete item with _item_id: {test_item_id_to_delete} from collection: {test_knowledge_id}")
  delete_result = weaviate_item_delete(knowledge_id=test_knowledge_id, item_id=test_item_id_to_delete)

  if delete_result:
    print(f"weaviate_item_delete test successful! Item '{test_item_id_to_delete}' deleted.")
    # Verify deletion
    final_count = collection.aggregate.over_all(total_count=True).total_count
    print(f"Final object count in '{test_knowledge_id}': {final_count}")

    # Check if the deleted item is truly gone
    from .weaviate_item_ready import weaviate_item_ready
    is_deleted_item_ready = weaviate_item_ready(knowledge_id=test_knowledge_id, item_id=test_item_id_to_delete)
    print(f"Is item '{test_item_id_to_delete}' ready after deletion? {is_deleted_item_ready}")
    
    is_kept_item_ready = weaviate_item_ready(knowledge_id=test_knowledge_id, item_id=test_item_id_to_keep)
    print(f"Is item '{test_item_id_to_keep}' ready after deletion? {is_kept_item_ready}")

  else:
    print("weaviate_item_delete test failed.")
  
  # Clean up the test collection
  client.collections.delete(test_knowledge_id)
  print(f"Cleaned up test collection: {test_knowledge_id}")
