import re
import tiktoken

class SmartMarkdownSplitter:
    def __init__(self, model_name="gpt-4o", max_tokens=1000, min_tokens=200):
        """
        初始化分割器
        :param model_name: 用於計算 token 的模型名稱
        :param max_tokens: 每個 chunk 的最大 token 數
        :param min_tokens: 每個 chunk 的理想最小 token 數 (儘量合併小區塊)
        """
        self.encoder = tiktoken.encoding_for_model(model_name)
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        
        # 定義分割優先順序 (從最粗的架構到最細的文字)
        self.separators = [
            r"\n# ",      # H1 標題
            r"\n## ",     # H2 標題
            r"\n### ",    # H3 標題
            r"\n[-*_]{3,}\s*\n", # 分隔線 (Horizontal Rules)
            r"\n\n",      # 段落
            r"\n\|\s*[-:]", # 表格的分隔線 (確保表格不被亂切)
            r"\n",        # 單換行
            r"。\s*",      # 中文句點
            r"\.\s*",      # 英文句點
            r" ",         # 空格
            r""           # 字元 (最後手段)
        ]

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

    def split(self, text):
        """主要執行方法：切分並智慧合併過小的區塊"""
        # 1. 執行遞迴切分
        initial_chunks = self._split_text_recursively(text, self.separators)
        
        # 2. 智慧合併 (處理 min_tokens)
        final_chunks = []
        current_chunk = ""
        
        for chunk in initial_chunks:
            chunk_tokens = self.count_tokens(chunk)
            current_tokens = self.count_tokens(current_chunk)
            
            # 如果目前 chunk 加上新的塊還在 max 範圍內，且目前太小，則合併
            if current_chunk and (current_tokens + chunk_tokens <= self.max_tokens):
                current_chunk += chunk
            else:
                if current_chunk:
                    final_chunks.append(current_chunk.strip())
                current_chunk = chunk
                
        if current_chunk:
            final_chunks.append(current_chunk.strip())
            
        return final_chunks
