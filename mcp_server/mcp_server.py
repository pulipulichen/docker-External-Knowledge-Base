import random
from typing import Dict
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

import os
from pathlib import Path
import yaml
import itertools

from search_knowledge_base import search_knowledge_base

MCP_API_KEY=os.getenv("MCP_API_KEY")

# 只允許這把 token
verifier = StaticTokenVerifier(
    tokens={
        MCP_API_KEY: {
            "client_id": "rps-client",
            "scopes": ["rps:play"],
        }
    },
    # 你要不要做 scope 管控都可以；先不控就留空或移除 required_scopes
    required_scopes=[],
)

mcp = FastMCP(name="external-knowledge-base", auth=verifier)

# ===========================

def load_knowledge_base_configs(directory):
    kb_list = []
    
    # 確保目錄存在
    if not directory.exists():
        print(f"錯誤: 找不到目錄 {directory}")
        return []

    # 搜尋所有 .yaml 檔案 (也可以視需求加入 .yml)
    # 使用 sorted 確保輸出順序一致
    
    yaml_files = sorted(
        itertools.chain(directory.glob("*.yml"), directory.glob("*.yaml"))
    )

    for file_path in yaml_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                
                # 1. 取得檔案名稱 (不含副檔名) 作為 name
                name = file_path.stem
                
                # 2. 取得內容裡的 description，若無則給預設值
                description = content.get('description', '無描述')
                
                # 3. 加入 Tuple 到列表
                kb_list.append((name, description))
                
        except Exception as e:
            print(f"讀取檔案 {file_path.name} 時發生錯誤: {e}")

    return kb_list

# 執行轉換
BASE_DIR = Path("/knowledge_base_configs")
knowledge_base_types = load_knowledge_base_configs(BASE_DIR)

# ===========================
def make_tool_function(reg_key, reg_desc):
    """
    這是一個 '函數工廠' (Function Factory)。
    它利用閉包 (Closure) 來鎖定 reg_key 的值。
    """
    
    # 定義工具函數，這裡的 reg_key 會被鎖定為當下的值
    def dynamic_tool(
        query: Annotated[
            str, 
            Field(description="想要查詢的具體問題或是關鍵字，可以是一段敘述，例如 '加班費如何計算'")
        ],
        top_k: Annotated[
            int, 
            Field(description="要返回的最佳匹配結果數量 (預設為 5)")
        ] = 5,
        score_threshold: Annotated[
            float, 
            Field(description="相似度分數門檻 (0.0 到 1.0)，低於此分數的結果將被忽略 (預設為 0.1)")
        ] = 0.1
    ) -> str:
        return search_knowledge_base(reg_key, query, top_k, score_threshold)
    
    # 【關鍵步驟 1】修改函數名稱
    # MCP (和 Python) 依賴函數名稱來識別工具。
    # 必須確保每個工具名稱唯一，例如: search_traffic_rules
    dynamic_tool.__name__ = f"search_{reg_key}_rules"
    
    # 【關鍵步驟 2】修改 Docstring (工具描述)
    # 這是 LLM 決定是否使用此工具的依據
    dynamic_tool.__doc__ = f"{reg_desc}。輸入想要查詢的關鍵字。"
    
    return dynamic_tool

# 開始迴圈註冊
for key, desc in knowledge_base_types:
    # 1. 產生函數
    tool_func = make_tool_function(key, desc)
    
    # 2. 手動呼叫 mcp.tool() 裝飾器來註冊
    # 在 Python 中，@decorator 其實就是 func = decorator(func)
    mcp.tool()(tool_func)

    print(f"已註冊工具: {tool_func.__name__}")

# ===========================

if __name__ == "__main__":
    # 這是讓伺服器運行的進入點
    mcp.run(transport="http", port=80, host="0.0.0.0")