import regex
def segment_text(content: str) -> str:
    """
    在中文與非數字英文的符號之間添加空格，並遞迴處理列表和字典。
    
    :param content: 可以是字串、列表或字典
    :return: 格式化後的內容
    """
    # print(content)

    if isinstance(content, list):
        return [segment_text(item) for item in content]
    elif isinstance(content, dict):
        return {key: segment_text(value) for key, value in content.items()}
    
    if not isinstance(content, str):
        return content  # 如果不是字串，則直接返回

    if not isinstance(content, str):
        return content  # 如果不是字串，則直接返回

    # 正則表達式處理 CJK 字元（中文）與符號
    def replace_func(match):
        char = match.group(0)
        if regex.match(r"[0-9\s]", char):  # 如果是數字或空格，不處理
            return char
        return f" {char} "  # 其他符號前後加空格

    result = regex.sub(r"([_\W]|\p{Han})", replace_func, content)

    # 過濾非法字符
    result = regex.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", " ", result)

    # 只保留單個空格
    result = regex.sub(r"\s+", " ", result).strip()

    return result