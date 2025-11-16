# Weaviate Integration

This package provides utilities for interacting with a Weaviate vector database, specifically for managing knowledge base collections and items.

## Modules

### `weaviate_add.py`
This module contains the `weaviate_add` function, which is responsible for adding data objects to a Weaviate collection. It takes a list of data rows, segments the document text, generates UUIDs, and inserts them into the specified collection.

### `weaviate_collection_delete.py`
This module provides the `weaviate_collection_delete` function, which allows for the deletion of an entire Weaviate collection based on its name (knowledge_id).

### `weaviate_item_delete.py`
The `weaviate_item_delete` module offers the `weaviate_item_delete` function to remove specific items from a Weaviate collection. It uses `item_id` (or `title`) to filter and delete the relevant data objects.

### `weaviate_item_ready.py`
This module includes the `weaviate_item_ready` function, which checks if a specific item exists within a Weaviate collection. It returns `True` if the item is found, and `False` otherwise.

### `weaviate_query.py`
The `weaviate_query` module provides the `weaviate_query` function for performing hybrid (text and vector) searches within a Weaviate collection. It supports various query configurations such as `query_alpha`, `max_results`, `score_threshold`, and `item_distinct` filtering, and returns relevant knowledge base responses.

----

# Mute logger

```py
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="weaviate")

import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpx_logger").setLevel(logging.WARNING)
logging.getLogger("weaviate").setLevel(logging.WARNING)
```