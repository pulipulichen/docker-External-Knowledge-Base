from .helper.get_collection import get_collection
from .helper.metadata_to_filters import metadata_to_filters
from .helper.get_client import get_client
from .weaviate_add import weaviate_add
import weaviate.classes as wvc

def weaviate_item_ready(**kwargs):

  collection_name = kwargs.get("knowledge_id", None)
  item_id = kwargs.get("item_id", kwargs.get("title", None))

  # print(query, collection_name)

  if item_id == None:
    return False
  
  filters = metadata_to_filters({
    "_item_id": item_id
  })

  # =================================================================

  collection = get_collection(collection_name)
  
  response = collection.data.fetch_objects(
    filters=filters,
    limit=1
  )

  return (len(response.objects) > 0)

if __name__ == "__main__":
  # This is a test usage example.
  test_knowledge_id = "test_knowledge_base_item_ready"
  test_item_id_exists = "doc_exists"
  test_item_id_not_exists = "doc_not_exists"

  client = get_client()
  # Clean up previous test data if it exists
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
      "chunk_id": "doc_exists_chunk1",
      "document": "This document should exist.",
      "vector": [0.1, 0.2, 0.3],
      "metadata": {"source": "exists.txt", "_item_id": test_item_id_exists}
    }
  ]
  weaviate_add(knowledge_id=test_knowledge_id, data_rows=test_data_rows)
  print(f"Added test data for item '{test_item_id_exists}' to '{test_knowledge_id}'.")

  print(f"Checking if item '{test_item_id_exists}' is ready in collection: {test_knowledge_id}")
  is_ready_exists = weaviate_item_ready(knowledge_id=test_knowledge_id, item_id=test_item_id_exists)
  print(f"Result for '{test_item_id_exists}': {is_ready_exists}")

  print(f"Checking if item '{test_item_id_not_exists}' is ready in collection: {test_knowledge_id}")
  is_ready_not_exists = weaviate_item_ready(knowledge_id=test_knowledge_id, item_id=test_item_id_not_exists)
  print(f"Result for '{test_item_id_not_exists}': {is_ready_not_exists}")

  if is_ready_exists and not is_ready_not_exists:
    print("weaviate_item_ready test successful!")
  else:
    print("weaviate_item_ready test failed.")
  
  # Clean up the test collection
  client.collections.delete(test_knowledge_id)
  print(f"Cleaned up test collection: {test_knowledge_id}")
