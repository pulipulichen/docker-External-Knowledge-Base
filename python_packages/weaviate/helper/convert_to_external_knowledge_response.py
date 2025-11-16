def convert_to_external_knowledge_response(results):
  records = []
  # print('bbb================================================================')
  # print(results)
  # print(len(results), score_threshold)
  for result in results:
    score = result.metadata.score
    title = result.properties["_item_id"]
    content = result.properties["_document"]

    metadata = result.properties
    del metadata["_item_id"]
    del metadata["_document"]
    del metadata["_index"]

    # Remove None values from metadata
    metadata = {k: v for k, v in metadata.items() if v is not None}

    records.append({'metadata': metadata,
      'score': score,
      'title': title,
      'content': content,
    })

  return {"records": records}
