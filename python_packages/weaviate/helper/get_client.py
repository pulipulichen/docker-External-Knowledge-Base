import weaviate
import os
import warnings
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType, Tokenization

client = None

weavite_host = os.getenv('WEAVIATE_HOST', 'weaviate')
weavite_port = int(os.getenv('WEAVIATE_PORT', '8080'))
weavite_grpc_port = int(os.getenv('WEAVIATE_GRPC_PORT', '50051'))

# 忽略 Weaviate 未正確關閉連線的警告
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*The connection to Weaviate was not closed properly.*")

# https://weaviate.io/developers/weaviate/connections/connect-local
def get_client():
  global client 

  if client is None or not client.is_connected():
    # url = f"http://{weavite_host}:{weavite_port}"
    # print("url", url)
    client = weaviate.connect_to_local(
      host=weavite_host, 
      port=weavite_port,
      grpc_port=weavite_grpc_port
    )  # 根據你的環境修改 URL

  return client
