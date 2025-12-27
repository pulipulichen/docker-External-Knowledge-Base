def convert_to_external_knowledge_response(knowledge_id, data_source_path, results):
  records = []
  # print('================================================================')
  # print(results)
  # print(len(results), score_threshold)

  for result in results:
    score = result.metadata.score
    title = result.properties["_chunk_id"]
    content = result.properties["_document"]

    metadata = result.properties
    if "path" not in metadata:
      metadata["path"] = data_source_path
    metadata["path"] = "https://blog.pulipuli.info/"
    metadata["description"] = knowledge_id
    # del metadata["_item_id"]
    del metadata["_document"]
    del metadata["_index"]
    del metadata["_chunk_id"]

    if "title" in metadata:
      title = metadata["title"]

    # Remove None values from metadata
    metadata = {k: v for k, v in metadata.items() if v is not None}

    records.append({'metadata': metadata,
      'score': score,
      'title': title,
      'content': content,
    })

  return {"records": records}
