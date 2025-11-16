from .helper.get_collection import get_collection
from .helper.get_client import get_client

from .helper.text_to_uuid import text_to_uuid
from .helper.segment_text import segment_text

import weaviate.classes as wvc
import os

def weaviate_add(**kwargs):

  collection_name = kwargs.get("knowledge_id", None)
  data_rows = kwargs.get("data_rows", [])
  
  if len(data_rows) == 0:
    return False
  
  # print(data_rows)

  collection = get_collection(collection_name)

  batch_products = []

  for data_row in data_rows:
    chunk_id = data_row.get('chunk_id', None)
    if chunk_id is None:
      continue

    uuid = text_to_uuid(chunk_id)

    document = data_row.get('document', None)
    if document is None:
      continue

    indexed_document = segment_text(document)

    vector = data_row.get('vector', [])
    if len(vector) == 0:
      continue

    metadata = data_row.get('metadata', {})
    metadata["_index"] = indexed_document
    metadata["_document"] = document

    metadata["_chunk_id"] = chunk_id
    # index = 

    # print({"properties": metadata})

    batch_products.append(
      wvc.data.DataObject(
        properties=metadata,
        uuid=uuid,
        vector=vector
      )
    )

  collection.data.insert_many(batch_products)

  print(f"Inserted {len(batch_products)} objects into Weaviate collection '{collection_name}'.")

  return True

if __name__ == "__main__":
  # This is a test usage example. In a real scenario, these values would come from your application.
  test_knowledge_id = "test_knowledge_base_add"

  test_data_rows = [
    {
      "chunk_id": "doc1_chunk1",
      "document": "This is the first part of document one.",
      "vector": [0.1, 0.2, 0.3],
      "metadata": {"source": "doc1.txt", "page": 1, "_item_id": "doc1"}
    },
    {
      "chunk_id": "doc1_chunk2",
      "document": "This is the second part of document one.",
      "vector": [0.4, 0.5, 0.6],
      "metadata": {"source": "doc1.txt", "page": 2, "_item_id": "doc1"}
    },
    {
      "chunk_id": "doc2_chunk1",
      "document": "This is the only part of document two.",
      "vector": [0.7, 0.8, 0.9],
      "metadata": {"source": "doc2.txt", "page": 1, "_item_id": "doc2"}
    },
  ]

  print(f"Attempting to add data to collection: {test_knowledge_id}")
  success = weaviate_add(knowledge_id=test_knowledge_id, data_rows=test_data_rows)

  if success:
    print("weaviate_add test successful!")
    # You can add verification steps here, e.g., query the collection to see if data was added.
  else:
    print("weaviate_add test failed.")
