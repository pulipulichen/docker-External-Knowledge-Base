import re
import tiktoken


def _encoder_for_model(model_name: str):
    """Resolve tiktoken encoder; fall back when encoding_for_model lacks the model."""
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        mn = (model_name or "").lower()
        if "gpt-4o" in mn:
            try:
                return tiktoken.get_encoding("o200k_base")
            except (KeyError, ValueError):
                # Old tiktoken: o200k_base missing ("Unknown encoding o200k_base")
                pass
        return tiktoken.get_encoding("cl100k_base")


_JSON_OBJECT_ARRAY_START = re.compile(r"^\s*\[\s*\{", re.DOTALL)
_JSON_OBJECT_ARRAY_END = re.compile(r"\}\s*\]\s*$", re.DOTALL)


def _looks_like_json_object_array(text: str) -> bool:
    """True if text looks like a top-level JSON array of objects: [{ ... }, ... ]."""
    if not text or not text.strip():
        return False
    s = text.strip()
    return bool(_JSON_OBJECT_ARRAY_START.search(s) and _JSON_OBJECT_ARRAY_END.search(s))


# Split between array elements without consuming the next object's leading "{".
_JSON_ARRAY_OBJECT_BOUNDARY = re.compile(r"(?<=\})\s*,\s*(?=\{)")


def _wrap_json_object_array_segment(segment: str) -> str:
    """
    Turn one slice from between-object splits into a valid single-element array: [{ ... }].
    First slice starts with "["; later slices start with "{"; last slice ends with "]".
    """
    s = segment.strip()
    if not s:
        return s
    if not s.startswith("["):
        s = "[" + s
    if not s.endswith("]"):
        s = s + "]"
    return s


def _join_wrapped_single_object_arrays(parts: list[str]) -> str:
    """Join multiple [{...}] strings into one JSON array [{...},{...},...]."""
    stripped = [p.strip() for p in parts if p.strip()]
    if len(stripped) == 1:
        return stripped[0]
    inners: list[str] = []
    for p in stripped:
        if not (p.startswith("[") and p.endswith("]")):
            raise ValueError("expected each part to be a wrapped single-element array [{...}]")
        inners.append(p[1:-1].strip())
    return "[" + ",".join(inners) + "]"


class SmartMarkdownSplitter:
    def __init__(self, model_name="gpt-4o", max_tokens=1000):
        """
        Splitter: pack consecutive segments up to max_tokens; start a new chunk when the next
        segment would exceed max_tokens.
        :param model_name: model name for tiktoken
        :param max_tokens: maximum tokens per output chunk
        """
        self.encoder = _encoder_for_model(model_name)
        self.max_tokens = max_tokens

        # Markdown-oriented order (coarse structure first).
        self._separators_markdown = [
            r"\n---\n",
            r"\n# ",
            r"\n## ",
            r"\n### ",
            r"\n[-*_]{3,}\s*\n",
            r"\n\n",
            r"\n\|\s*[-:]",
            r"\n",
            r"。\s*",
            r"\.\s*",
            r" ",
            r"",
        ]
        # After object boundaries (handled in _split_json_object_array), split huge objects.
        self._separators_json_object_array_inner = [
            r"\n\n",
            r"\n",
            r"。\s*",
            r"\.\s*",
            r" ",
            r"",
        ]
        self.separators = self._separators_markdown

    def count_tokens(self, text):
        """精確計算 Token 數量"""
        return len(self.encoder.encode(text))

    def _split_text_recursively(self, text, separators):
        """遞迴切分邏輯，盡可能保留高層級結構"""
        if self.count_tokens(text) <= self.max_tokens:
            return [text]

        if not separators:
            # 如果沒有分隔符了，硬性切分（保險機制）
            tokens = self.encoder.encode(text)
            return [self.encoder.decode(tokens[i:i + self.max_tokens]) 
                    for i in range(0, len(tokens), self.max_tokens)]

        # 嘗試目前最高級別的分隔符
        current_sep = separators[0]
        splits = []
        
        # 使用 Regex 切分但保留分隔符
        raw_splits = re.split(f"({current_sep})", text)
        
        # 重新組合分隔符與內容
        curr_part = ""
        for i in range(0, len(raw_splits), 2):
            part = raw_splits[i]
            sep = raw_splits[i+1] if i+1 < len(raw_splits) else ""
            combined = part + sep
            
            if self.count_tokens(curr_part + combined) <= self.max_tokens:
                curr_part += combined
            else:
                if curr_part:
                    splits.append(curr_part)
                # 如果單一區塊連一個分隔符內容都塞不下，則進入下一層遞迴
                if self.count_tokens(combined) > self.max_tokens:
                    splits.extend(self._split_text_recursively(combined, separators[1:]))
                    curr_part = ""
                else:
                    curr_part = combined
        
        if curr_part:
            splits.append(curr_part)
            
        return splits

    def _split_json_object_array(self, text: str) -> list[tuple[str, bool]]:
        """
        Split on object boundaries. Each wrapped one-object array is mergeable=True;
        oversized segments split via recursion are mergeable=False (not valid [{...}]).
        """
        segments = _JSON_ARRAY_OBJECT_BOUNDARY.split(text)
        out: list[tuple[str, bool]] = []
        for seg in segments:
            s = seg.strip()
            if not s:
                continue
            if self.count_tokens(s) <= self.max_tokens:
                out.append((_wrap_json_object_array_segment(s), True))
            else:
                sub = self._split_text_recursively(s, self._separators_json_object_array_inner)
                for c in sub:
                    out.append((c.strip(), False))
        return out

    def _merge_json_object_array_up_to_max(
        self, items: list[tuple[str, bool]]
    ) -> list[str]:
        """Greedily merge adjacent mergeable [{...}] pieces while total tokens <= max_tokens."""
        result: list[str] = []
        n = len(items)
        i = 0

        while i < n:
            chunk, mergeable = items[i]
            if not mergeable:
                result.append(chunk)
                i += 1
                continue

            run: list[str] = [chunk]
            i += 1
            joined = _join_wrapped_single_object_arrays(run)
            run_tokens = self.count_tokens(joined)

            while i < n and items[i][1]:
                nxt = items[i][0]
                trial = _join_wrapped_single_object_arrays(run + [nxt])
                trial_tokens = self.count_tokens(trial)
                if trial_tokens > self.max_tokens:
                    break
                run.append(nxt)
                joined = trial
                run_tokens = trial_tokens
                i += 1

            result.append(joined)

        return result

    def split(self, text):
        """Split text; merge consecutive parts greedily up to max_tokens per chunk."""
        is_json_object_array = _looks_like_json_object_array(text)
        if is_json_object_array:
            self.separators = self._separators_json_object_array_inner
            tagged = self._split_json_object_array(text)
            merged = self._merge_json_object_array_up_to_max(tagged)
            return [c.strip() for c in merged if c.strip()]

        self.separators = self._separators_markdown
        initial_chunks = self._split_text_recursively(text, self.separators)

        final_chunks = []
        current_chunk = ""

        for chunk in initial_chunks:
            chunk_tokens = self.count_tokens(chunk)
            current_tokens = self.count_tokens(current_chunk)

            if current_chunk and (current_tokens + chunk_tokens <= self.max_tokens):
                current_chunk += chunk
            else:
                if current_chunk:
                    final_chunks.append(current_chunk.strip())
                current_chunk = chunk

        if current_chunk:
            final_chunks.append(current_chunk.strip())

        return final_chunks
