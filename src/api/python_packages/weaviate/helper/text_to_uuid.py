
import uuid

def text_to_uuid(text):
    """
    將任意文字轉換為 UUID（類似 99e870ac-2c01-47a3-a1c2-fa4e07ab0977 格式）
    使用 UUID5（SHA-1 雜湊）確保相同輸入產生相同的 UUID。
    
    :param text: 任意輸入文字
    :return: 轉換後的 UUID 字串
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, text))