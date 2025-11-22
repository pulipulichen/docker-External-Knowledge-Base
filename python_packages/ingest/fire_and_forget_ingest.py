import threading
import asyncio

from .ingest import ingest_data

def fire_and_forget_ingest(knowledge_id: str, section_name: str, force_update: False):
    def runner():
        # 每個 thread 自己開一個 event loop
        asyncio.run(ingest_data(knowledge_id, section_name, force_update))

    t = threading.Thread(target=runner, daemon=True)
    t.start()
