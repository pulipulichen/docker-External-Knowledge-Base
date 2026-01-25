import requests
import os
import json

def search_knowledge_base(knowledge_id: str, query: str, top_k: int = 5, score_threshold: float = 0.1):
    # API 端點
    url = "http://api/retrieval"

    # 從環境變數獲取 API KEY，如果沒有設置，請替換第二個參數為您的實際 Key
    api_key = os.environ.get("MCP_API_KEY")

    # 設定 HTTP Headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 準備請求的資料 (Payload)
    payload = {
        "knowledge_id": knowledge_id,
        "query": query,
        "retrieval_setting": {
            "top_k": top_k,
            "score_threshold": score_threshold
        }
    }

    print(json.dumps(payload, indent=4, ensure_ascii=False))

    try:
        # 發送 POST 請求
        # json=payload 會自動將字典轉換為 JSON 字串並設定正確的 Content-Type
        response = requests.post(url, headers=headers, json=payload)

        # 檢查回應狀態碼 (如果是 4xx 或 5xx 會拋出例外)
        response.raise_for_status()

        # 解析並印出回應的 JSON 結果
        result = response.json()
        print("查詢成功，回應如下:")
        print(json.dumps(result, indent=4, ensure_ascii=False))
        return json.dumps(result, ensure_ascii=False)

    except requests.exceptions.RequestException as e:
        print(f"請求發生錯誤: {e}")
        # 如果有回應內容，也印出來幫助除錯
        if 'response' in locals() and response.content:
             print(f"錯誤詳情: {response.text}")

        return json.dumps({
            "error": str(e)
        }, ensure_ascii=False)

if __name__ == "__main__":
    search_knowledge_base()