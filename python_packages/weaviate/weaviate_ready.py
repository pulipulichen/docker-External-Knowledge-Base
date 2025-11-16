from .helper.is_collection_existed import is_collection_existed
import weaviate.classes as wvc

def weaviate_ready(**kwargs):

  collection_name = kwargs.get("knowledge_id", None)
  
  # =================================================================

  return is_collection_existed(collection_name)

if __name__ == "__main__":
  # This is a test usage example for weaviate_ready.
  test_collection_name = "test_collection_ready"

  print(f"Checking if collection '{test_collection_name}' is ready:")
  is_ready_before_create = weaviate_ready(knowledge_id=test_collection_name)
  print(f"Result: {is_ready_before_create}")
