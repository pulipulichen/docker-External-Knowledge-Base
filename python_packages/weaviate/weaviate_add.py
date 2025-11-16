from .helper.get_collection import get_collection

from .helper.text_to_uuid import text_to_uuid
from .helper.segment_text import segment_text

import weaviate.classes as wvc

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
  