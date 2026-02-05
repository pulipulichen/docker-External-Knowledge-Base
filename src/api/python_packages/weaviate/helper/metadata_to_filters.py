from weaviate.classes.query import Filter

def metadata_to_filters(metadata = {}):
  filters = None

  conditions = []
  for key, value in metadata.items():
      if isinstance(value, str) and value[0:1] == '*' and value[-1] == '*':
        conditions.append(Filter.by_property(key).like(value))
      else:
        conditions.append(Filter.by_property(key).equal(value))
  # filters=Filter.by_property("category").equal("音響設備")
      
  if len(conditions) == 1:
    filters = conditions[0]
  elif len(conditions) > 1:
    filters = (Filter.all_of(conditions))

  return filters