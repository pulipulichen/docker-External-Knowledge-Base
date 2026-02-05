# 1. 指定 Base Image
FROM semitechnologies/weaviate:1.32.16-31de226.amd64

# 2. 設定環境變數 (Environment Variables)
# 注意：這些變數會直接寫入映像檔中
ENV QUERY_DEFAULTS_LIMIT=100
ENV AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED='true'
ENV PERSISTENCE_DATA_PATH="/var/lib/weaviate"
ENV CLUSTER_HOSTNAME='node1'

# 關於 WEAVIATE_LD_API_KEY:
# 安全性建議：不要將 API Key 直接寫死 (Hardcode) 在 Dockerfile 的 ENV 中，
# 這樣會導致金鑰洩漏在映像檔層 (Image Layers) 裡。
# 建議在 docker run 時動態傳入，但如果你是為了測試方便，可以取消下面這行的註解：
# ENV WEAVIATE_LD_API_KEY="你的_KEY"

# 3. 設定 Healthcheck
HEALTHCHECK --interval=10s \
            --timeout=5s \
            --retries=20 \
            --start-period=30s \
    CMD curl -sf http://localhost:8080/v1/.well-known/ready || exit 1

# Base image 已經包含預設的 ENTRYPOINT 和 CMD，
# 這裡不需要額外撰寫，它會自動啟動 Weaviate。