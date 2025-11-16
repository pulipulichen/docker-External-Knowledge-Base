from .helper.is_collection_existed import is_collection_existed
from .helper.get_client import get_client
from .helper.get_collection import get_collection
import weaviate.classes as wvc

def weaviate_ready(**kwargs):

  collection_name = kwargs.get("knowledge_id", None)
  
  # =================================================================

  is_existed = is_collection_existed(collection_name)

  if not is_existed:
    return False

  collection = get_collection(collection_name)
  if not collection:
    return False

  try:
    count = collection.aggregate.over_all(total_count=True).total_count
    return count > 1
  except Exception as e:
    print(f"Error getting collection count for {collection_name}: {e}")
    return False

if __name__ == "__main__":
  # This is a test usage example for weaviate_ready.
  test_collection_name = "test_collection_ready"

  print(f"Checking if collection '{test_collection_name}' is ready:")
  is_ready_before_create = weaviate_ready(knowledge_id=test_collection_name)
  print(f"Result: {is_ready_before_create}")

  # Test case for a non-existent collection
  non_existent_collection = "non_existent_collection_12345"
  print(f"\nChecking if collection '{non_existent_collection}' is ready:")
  is_ready_non_existent = weaviate_ready(knowledge_id=non_existent_collection)
  print(f"Result: {is_ready_non_existent}")

  # Test case for a collection with 0 or 1 item (should return False)
  # For this, you would typically need to create a collection and add 0 or 1 item.
  # This example assumes a collection with 0 or 1 item would return False.
  # To properly test this, you'd need to mock or actually create a collection with specific item counts.
  # For now, we'll just simulate the expected output.
  print(f"\nSimulating check for collection with <= 1 item:")
  # Assuming 'test_collection_ready' might have 0 or 1 item for this test
  # In a real scenario, you'd create a collection and control its item count.
  # For demonstration, let's assume a collection named 'single_item_collection' exists with 1 item.
  # If weaviate_ready returns True for 'test_collection_ready' it means it has > 1 item.
  # If it returns False, it means it has <= 1 item or doesn't exist.
  # For a more robust test, you'd need to set up a Weaviate instance and populate it.
  # For now, the existing test_collection_ready will serve as a basic check.
