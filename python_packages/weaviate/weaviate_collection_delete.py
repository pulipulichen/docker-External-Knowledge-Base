from .helper.get_client import get_client
from .weaviate_add import weaviate_add
import weaviate.classes as wvc
import os

def weaviate_collection_delete(**kwargs):

  collection_name = kwargs.get("knowledge_id", None)
  
  if collection_name is None:
    collection_name = os.getenv('DATABASE_COLLECTION_NAME', 'knowledge_base')

  client = get_client()
  if client.collections.exists(collection_name):
    return client.collections.delete(collection_name)

  return False

if __name__ == "__main__":
  # This is a test usage example.
  test_knowledge_id = "test_knowledge_base_delete"

  # Ensure there's a collection to delete for testing
  print(f"Ensuring collection '{test_knowledge_id}' exists for deletion test...")
  client = get_client()
  if not client.collections.exists(test_knowledge_id):
    # Create a dummy collection and add some data
    client.collections.create(
      name=test_knowledge_id,
      vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(),
      generative_config=wvc.config.Configure.Generative.openai(),
    )
    weaviate_add(
      knowledge_id=test_knowledge_id,
      data_rows=[
        {
          "chunk_id": "temp_doc_chunk1",
          "document": "Temporary document for deletion test.",
          "vector": [0.1, 0.1, 0.1],
          "metadata": {"source": "temp.txt", "_item_id": "temp_doc"}
        }
      ]
    )
    print(f"Collection '{test_knowledge_id}' created with dummy data.")
  else:
    print(f"Collection '{test_knowledge_id}' already exists.")

  print(f"Attempting to delete collection: {test_knowledge_id}")
  success = weaviate_collection_delete(knowledge_id=test_knowledge_id)

  if success:
    print(f"weaviate_collection_delete test successful! Collection '{test_knowledge_id}' deleted.")
    # Verify deletion
    if not client.collections.exists(test_knowledge_id):
      print("Verification: Collection no longer exists.")
    else:
      print("Verification: Collection still exists (deletion might have failed).")
  else:
    print("weaviate_collection_delete test failed or collection did not exist.")
