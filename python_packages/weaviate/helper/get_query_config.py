import os
def get_query_config(query_config = {}):
  # print(query_config)
  if query_config is None:
    query_alpha = {}

  max_results = int(os.getenv('DATABASE_QUERY_MAX_RESULTS', 5))
  if 'max_results' in query_config:
    max_results = int(query_config['max_results'])

  if 'top_k' in query_config:
    max_results = int(query_config['top_k'])

  result_width = int(os.getenv('DATABASE_QUERY_RESULT_WIDTH', 30))
  if 'result_width' in query_config:
    result_width = int(query_config['result_width'])

  item_distinct = os.getenv('DATABASE_QUERY_ITEM_DISTINCT', True)
  if item_distinct == False or item_distinct == 'false' or item_distinct == 'False':
    item_distinct = False
  if 'item_distinct' in query_config:
    item_distinct = bool(query_config['item_distinct'])
  
  # print(item_distinct, os.getenv('DATABASE_QUERY_ITEM_DISTINCT', True), bool('false'))
  # item_distinct = True

  score_threshold = float(os.getenv('DATABASE_QUERY_SCORE_THRESHOLD', 0.0))
  if 'score_threshold' in query_config:
    score_threshold = float(query_config['score_threshold'])

  offset = 0
  if 'offset' in query_config:
    offset = int(query_config['offset'])


  query_alpha = float(os.getenv('DATABASE_QUERY_ALPHA', 0.5))
  if 'query_alpha' in query_config:
    query_alpha = float(query_config['query_alpha'])

  return {
    'max_results': max_results,
    'result_width': result_width,
    'item_distinct': item_distinct,
    'score_threshold': score_threshold,
    'query_alpha': query_alpha,
    'offset': offset
  }