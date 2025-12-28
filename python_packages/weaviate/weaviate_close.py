from .helper.get_client import get_client

def weaviate_close(**kwargs):
  client = get_client()
  
  if client:
    try:
      client.close()
      return True
    except Exception as e:
      print(f"Error closing Weaviate client: {e}")
      return False
  
  return False

if __name__ == "__main__":
  print("Closing Weaviate client...")
  result = weaviate_close()
  print(f"Result: {result}")
