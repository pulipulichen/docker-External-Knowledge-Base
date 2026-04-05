# 知識庫設定檔（`knowledge_base/configs/*.yml`）

每個知識庫對應**一個** YAML 檔，檔名（不含副檔名）就是 API／檢索時使用的 **`knowledge_id`**。例如 `example.yml` → `knowledge_id` 為 `example`。

服務會掃描此目錄下所有 `.yml` / `.yaml`，`GET /knowledge-ids` 回傳的即為這些檔名主檔名。

---

## 與 `knowledge_id` 相關的兩件事

### 1. 檔名 = 設定的主鍵

程式會讀取：

`src/api/python_packages/knowledge_base_config/get_knowledge_base_config.py`

路徑規則：`knowledge_base/configs/{knowledge_id}.yml`（若無則嘗試 `.yaml`）。

### 2. 試算表：用 `!` 指定工作表（分頁）

若資料來源是 **ODS／XLSX／Google 試算表**（轉成 xlsx 下載），每一個工作表名稱會對應一組向量索引。呼叫檢索時可以用：

`{設定檔主檔名}!{工作表名稱}`

例如：`example!Sheet1`。

解析邏輯在 `parse_knowledge_id`：只會依**最後一個** `!` 切開。

- `my_kb!庫存` → `knowledge_id = my_kb`，`section_name = 庫存`
- 若 ID 裡本身有多個 `!`，只有**最後一段**當工作表名稱，其餘仍屬於檔名主鍵的一部分（例如 `a!b!Sheet2` → `knowledge_id = a!b`，`section_name = Sheet2`）

若請求裡**沒有**帶 `!`，則工作表名稱取自設定里的 **`section`** 鍵；若也沒設，則由程式從檔案推斷第一個工作表（見 `get_section_name`）。

---

## 必填／核心欄位：`path`

`path` 描述「資料從哪裡來」，行為由 `get_knowledge_base_config` 整理後，會衍生 `file_name`、`file_path`、`is_url`、`is_file`、`markdown_convertable` 等內部欄位。

| `path` 型態 | 說明 |
|-------------|------|
| `http://` 或 `https://` | 視為網址。若為 **Google 試算表**連結，會改成可下載的 **xlsx** URL，本地儲存檔名變成 `{knowledge_id}.xlsx`。**Google 文件／簡報**會改成可下載的 **Markdown** 流程。一般網址則不轉換。 |
| 以 `.md`、`.ods`、`.xlsx` 結尾 | 視為放在 `knowledge_base/files/` 底下的**檔名**（`file_name` 等於此字串）。 |
| 其他字串 | 若 `knowledge_base/files/{path}` **不是**已存在的檔案，則視為**資料夾路徑**（`is_file` 為 false），走目錄索引流程（搭配 `include_ext`）。若是已存在的檔案則依檔案處理。 |

實際儲存與索引用的檔案路徑多在 `knowledge_base/files/` 下；下載或轉換後的檔名會依上面規則決定。

---

## 常用選填欄位

### `description`

人類可讀說明。MCP 服務載入設定列表時會用來當工具描述；不影響索引邏輯。

### `section`（試算表／多工作表情境）

- 當 API **沒有**使用 `knowledge_id!工作表` 語法時，預設要讀的工作表名稱可寫在這裡。
- 若設了 `section`，Weaviate 里的集合／物件 ID 會固定成 **`{knowledge_id}`**（不再附加 `_工作表名`），與「每工作表一個 `knowledge_id_工作表`」的模式不同。專案里 `goods_item.yml` 即為固定 `section` 的範例。

### `include_fileds`（注意拼字）

僅在從 **ODS／XLSX** 轉成列資料時有效。列出要保留的**欄位名稱**（需與試算表第一列標題一致）。程式里讀取的鍵名是 **`include_fileds`**（`filed` 為既有拼字，請與程式一致）。

### `include_ext`

當 `path` 指向**資料夾**（目錄索引）時，列出要納入的副檔名，例如：

```yaml
include_ext:
  - html
```

### `auto_update`

巢狀物件，目前程式**實際會讀**的主要是：

- **`delay_seconds`**：節流「多久內不要重複下載／轉檔／視為不需重建索引」。預設邏輯里若缺省，多處會退回 **30 分鐘（1800 秒）**。
- 設為 **`-1`** 且本機目標檔已存在時，下載流程會直接略過（見 `download_file`）。

設定檔里常見的 **`enable: true`** 在目前程式碼中**沒有被讀取**，不會單獨關閉自動更新；實際是否重跑仍依 `force_update` 與上述時間間隔判斷。

### `index`

巢狀物件，控制索引寫入 Weaviate 的方式。

| 子鍵 | 說明 |
|------|------|
| **`mode`** | `all`（預設）：每次把本輪取得的 chunks **全部**寫入。`last`：只取「最後一段」chunks 再寫入（段落長度由 `length` 決定）。若 Weaviate 端尚未就緒，`last` 會退回與 `all` 類似的行為（見 `index_mode_last`）。 |
| **`length`** | 搭配 `mode: last` 時，取 chunks 清單的**最後**幾筆（預設 100）。 |
| **`max_tokens`** | 範例 YAML 中放在 `index` 底下，意圖是限制 Markdown 分段時的 token 上限；但目前 `get_chunks_from_markdown` 使用 `config.get('index.max_tokens', …)` 的寫法**無法**讀到巢狀的 `index: max_tokens`，實際上會一直使用程式內建預設值。若未來修正為讀取 `index.max_tokens` 巢狀鍵，此欄位才會生效。 |

---

## 資料如何變成 chunks（對照 `path`）

- **`.ods` / `.xlsx`（含 Google 表轉成 xlsx）**：列 = 一筆 chunk，內容為該列欄位 JSON；工作表由 `!工作表名` 或 `section` 或預設第一張表決定。
- **`.md`**：由 Markdown 檔分段（token 相關見上節 `max_tokens` 說明）。
- **資料夾**：透過目錄索引與 `include_ext` 等流程轉成可索引內容。

---

## 最小範例

**Google 試算表（常見）：**

```yaml
path: https://docs.google.com/spreadsheets/d/…/edit
description: 說明文字
auto_update:
  enable: true
  delay_seconds: 86400
embedding_model: bge-m3
index:
  mode: last
  length: 100
```

**本機試算表檔：**

```yaml
path: mydata.ods
description: 說明
section: 工作表1
include_fileds:
  - 欄位A
  - 欄位B
auto_update:
  delay_seconds: 30
```

**本機目錄（HTML 等）：**

```yaml
path: my_docs_folder
description: 說明
auto_update:
  delay_seconds: 30
include_ext:
  - html
```

---

## 想再深入時可對照的程式位置

| 主題 | 檔案 |
|------|------|
| 載入 YAML、解析 `path` | `src/api/python_packages/knowledge_base_config/get_knowledge_base_config.py` |
| `knowledge_id!section` | `src/api/python_packages/knowledge_base_config/parse_knowledge_id.py` |
| 預設工作表名稱 | `src/api/python_packages/knowledge_base_config/get_section_name.py` |
| 試算表 → chunks | `src/api/python_packages/index/chunk/get_chunks_from_sheet.py` |
| 索引模式 all / last | `src/api/python_packages/index/mode/index_mode_all.py`、`index_mode_last.py` |
| 檢索時 Weaviate 的 `item_id` | `src/api/python_packages/retrieval/db_retrieval.py`（與 `section`、`is_file` 有關） |

HTTP 請求格式仍以 [documents/API.md](./API.md) 為準。
