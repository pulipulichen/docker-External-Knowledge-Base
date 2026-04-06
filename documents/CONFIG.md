# Knowledge base configuration (`knowledge_base/configs/*.yml`)

Each knowledge base maps to **one** YAML file. The filename (without extension) is the **`knowledge_id`** used by the API and retrieval. For example, `example.yml` → `knowledge_id` is `example`.

The service scans all `.yml` / `.yaml` files in this directory; `GET /knowledge-ids` returns those basenames.

---

## Two things tied to `knowledge_id`

### 1. Filename = primary key for config

The code loads config from:

`src/api/python_packages/knowledge_base_config/get_knowledge_base_config.py`

Path rule: `knowledge_base/configs/{knowledge_id}.yml` (falls back to `.yaml` if missing).

### 2. Spreadsheets: use `!` to pick a worksheet (tab)

If the source is **ODS / XLSX / Google Sheets** (downloaded as xlsx), each worksheet name maps to its own vector index. At query time you can use:

`{config_basename}!{worksheet_name}`

Example: `example!Sheet1`.

Parsing is in `parse_knowledge_id`: only the **last** `!` splits the string.

- `my_kb!Inventory` → `knowledge_id = my_kb`, `section_name = Inventory`
- If the ID contains multiple `!`, only the **final segment** is the worksheet name; the rest stays part of the basename key (e.g. `a!b!Sheet2` → `knowledge_id = a!b`, `section_name = Sheet2`)

If the request **does not** include `!`, the worksheet name comes from the **`section`** key in the config; if unset, the code infers the first sheet from the file (see `get_section_name`).

---

## Required / core field: `path`

`path` describes where data comes from. After `get_knowledge_base_config` normalizes it, internal fields such as `file_name`, `file_path`, `is_url`, `is_file`, and `markdown_convertable` are derived.

| `path` shape | Behavior |
|--------------|----------|
| `http://` or `https://` | Treated as a URL. **Google Sheets** links are rewritten to a downloadable **xlsx** URL; the local filename becomes `{knowledge_id}.xlsx`. **Google Docs / Slides** use a downloadable **Markdown** flow. Ordinary URLs are left as-is. |
| Ends with `.md`, `.ods`, or `.xlsx` | Treated as a **filename** under `knowledge_base/files/` (`file_name` equals this string). |
| Any other string | If `knowledge_base/files/{path}` is **not** an existing file, it is treated as a **directory path** (`is_file` is false) and the directory-indexing flow runs (with `include_ext`). If it is an existing file, it is handled as a file. |

Indexed files usually live under `knowledge_base/files/`; downloaded or converted filenames follow the rules above.

---

## Common optional fields

### `description`

Human-readable text. The MCP service uses it as the tool description when loading the config list; it does not affect indexing logic.

### `section` (spreadsheets / multi-sheet)

- When the API **does not** use `knowledge_id!worksheet` syntax, the default sheet name can be set here.
- If `section` is set, Weaviate collection / object IDs stay **`{knowledge_id}`** (no `_worksheet` suffix), unlike the “one `knowledge_id_worksheet` per sheet” pattern. The project’s `goods_item.yml` is an example of a fixed `section`.

### `include_fileds` (spelling note)

Only applies when converting **ODS / XLSX** to row records. Lists **column names** to keep (must match the first-row headers). The key in code is **`include_fileds`** (`filed` is the legacy spelling—match the code).

### `include_ext`

When `path` points at a **folder** (directory indexing), list extensions to include, for example:

```yaml
include_ext:
  - html
```

### `auto_update`

Nested object. What the code **actually reads** today is mainly:

- **`delay_seconds`**: Throttle “how long before we skip redundant download / conversion / index rebuild.” If omitted, many call sites default to **30 minutes (1800 seconds)**.
- Set to **`-1`** when the local target file already exists to skip download (see `download_file`).

The common **`enable: true`** in YAML is **not read** by current code and does not toggle auto-update alone; whether a run happens still depends on `force_update` and the interval above.

### `index`

Nested object; controls how chunks are written to Weaviate.

| Sub-key | Description |
|---------|-------------|
| **`mode`** | `all` (default): write **all** chunks from the current run. `last`: write only the **last** chunk segment (segment size from `length`). If Weaviate is not ready, `last` falls back to behavior similar to `all` (see `index_mode_last`). |
| **`length`** | With `mode: last`, take the **last** N chunks from the list (default 100). |
| **`max_tokens`** | Example YAMLs nest this under `intent` to cap tokens when splitting Markdown; but `get_chunks_from_markdown` uses `config.get('index.max_tokens', …)`, which **does not** read nested `index: max_tokens`, so the built-in default always applies until the code is fixed to read `index.max_tokens`. |

---

## How data becomes chunks (by `path`)

- **`.ods` / `.xlsx` (including Google Sheets as xlsx)**: One row = one chunk, payload is that row as JSON; sheet comes from `!sheet`, `section`, or the first sheet by default.
- **`.md`**: Split from the Markdown file (token limits: see `max_tokens` above).
- **Folder**: Directory indexing with `include_ext` (and related logic) produces indexable content.

---

## Minimal examples

**Google Sheets (common):**

```yaml
path: https://docs.google.com/spreadsheets/d/…/edit
description: Human-readable summary
auto_update:
  enable: true
  delay_seconds: 86400
embedding_model: bge-m3
index:
  mode: last
  length: 100
```

**Local spreadsheet file:**

```yaml
path: mydata.ods
description: Summary
section: Sheet1
include_fileds:
  - ColumnA
  - ColumnB
auto_update:
  delay_seconds: 30
```

**Local directory (HTML, etc.):**

```yaml
path: my_docs_folder
description: Summary
auto_update:
  delay_seconds: 30
include_ext:
  - html
```

---

## Code references for deeper reading

| Topic | File |
|-------|------|
| Load YAML, resolve `path` | `src/api/python_packages/knowledge_base_config/get_knowledge_base_config.py` |
| `knowledge_id!section` | `src/api/python_packages/knowledge_base_config/parse_knowledge_id.py` |
| Default worksheet name | `src/api/python_packages/knowledge_base_config/get_section_name.py` |
| Spreadsheet → chunks | `src/api/python_packages/index/chunk/get_chunks_from_sheet.py` |
| Index modes all / last | `src/api/python_packages/index/mode/index_mode_all.py`, `index_mode_last.py` |
| Weaviate `item_id` at retrieval | `src/api/python_packages/retrieval/db_retrieval.py` (related to `section`, `is_file`) |

HTTP request shapes are defined in [documents/API.md](./API.md).
