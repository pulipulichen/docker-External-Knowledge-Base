
def filter_item_distinct(response):
  # return response.objects
  # print(response)
  # 過濾重複的 item_id
  unique_results = {}
  for item in response.objects:
      item_id = item["_item_id"]
      # item_id = item.properties["category"]
      # print(item_id)
      if item_id not in unique_results:
          unique_results[item_id] = item  # 只保留第一個出現的

  # 轉換成列表輸出
  final_results = list(unique_results.values())
  return final_results