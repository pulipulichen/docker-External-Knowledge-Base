from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

import os
from pathlib import Path
import yaml
import itertools

from typing import Annotated
from pydantic import Field  # 新增引用

from search_knowledge_base import search_knowledge_base
from scrape_web_page import scrape_web_page
from search_web import search_web

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


def scrape_web_page_tool(
    url: Annotated[
        str,
        Field(
            description="要擷取主要內容的網頁 URL（文章、新聞、部落格等）",
        ),
    ],
    content_type: Annotated[
        str | None,
        Field(
            description="選填：傳給 Mercury Parser 的 contentType 查詢參數",
        ),
    ] = None,
    headers: Annotated[
        str | None,
        Field(
            description="選填：URL 編碼後的 HTTP headers 字串（見 mercury-parser API 文件）",
        ),
    ] = None,
) -> str:
    """使用 Mercury Parser 擷取網頁主要內容（標題、正文 HTML、摘要等），適合閱讀與後續引用。"""
    return scrape_web_page(url, content_type, headers)


scrape_web_page_tool.__name__ = "scrape_web_page"
mcp.tool()(scrape_web_page_tool)
print(f"已註冊工具: {scrape_web_page_tool.__name__}")

# ===========================


def search_web_tool(
    query: Annotated[
        str,
        Field(description="網路搜尋關鍵字或完整問句"),
    ],
    categories: Annotated[
        str | None,
        Field(
            description="選填：SearXNG 分類（例如 general、images、news）",
        ),
    ] = None,
    language: Annotated[
        str | None,
        Field(
            description="選填：語言代碼（例如 zh-TW、en）",
        ),
    ] = None,
    pageno: Annotated[
        int,
        Field(description="結果頁碼，從 1 開始"),
    ] = 1,
    safesearch: Annotated[
        int | None,
        Field(description="選填：安全搜尋 0=關、1=中、2=嚴格"),
    ] = None,
    time_range: Annotated[
        str | None,
        Field(
            description="選填：時間範圍（例如 day、week、month、year）",
        ),
    ] = None,
) -> str:
    """透過 SearXNG 搜尋公開網頁，取得標題、URL、摘要等結果。"""
    return search_web(
        query,
        categories=categories,
        language=language,
        pageno=pageno,
        safesearch=safesearch,
        time_range=time_range,
    )


search_web_tool.__name__ = "search_web"
mcp.tool()(search_web_tool)
print(f"已註冊工具: {search_web_tool.__name__}")

# ===========================

if __name__ == "__main__":
    # 這是讓伺服器運行的進入點
    mcp.run(transport="http", port=80, host="0.0.0.0")