import os
import sys

# Manually load .env BEFORE any imports from python_packages
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v.strip('"').strip("'")

import json
from python_packages.index.chunk.utils.sheet_to_json import sheet_to_json
import python_packages.image_describe.image_describe as id_module

# Mock Redis for testing environment
class MockRedis:
    def get(self, *args, **kwargs): return None
    def setex(self, *args, **kwargs): pass
id_module.redis_client = MockRedis()

def verify():
    filepath = 'knowledge_base_files/shopping_cart.ods'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"Processing {filepath}...")
    headers = ["網址", "價格", "商品名稱", "顏色", "尺寸", "圖片"]
    result = sheet_to_json(filepath, header_row=1)
    
    print(f"Total rows processed: {len(result)}")
    for i, row in enumerate(result[:5]):
        print(f"\nRow {i+1}:")
        print(f"  Keys: {list(row.keys())}")
        for key, value in row.items():
            if isinstance(value, dict) and "images_description" in value:
                print(f"  {key}: [IMAGE DESC] {value['images_description'][:100]}...")
            else:
                print(f"  {key}: {str(value)[:100]}...")

if __name__ == "__main__":
    verify()
