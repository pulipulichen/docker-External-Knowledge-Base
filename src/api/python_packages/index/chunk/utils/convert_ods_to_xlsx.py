import subprocess
import os
import shutil
import tempfile

def convert_ods_to_xlsx(ods_path, xlsx_path):
    """
    將 ods 檔案轉換成 xlsx 檔案
    使用系統中的 libreoffice 指令進行轉換
    """
    if not os.path.exists(ods_path):
        return False

    # 確保輸入路徑是絕對路徑
    ods_path = os.path.abspath(ods_path)
    xlsx_path = os.path.abspath(xlsx_path)
    
    # 取得 xlsx 的目錄與檔名
    xlsx_dir = os.path.dirname(xlsx_path)
    xlsx_filename = os.path.basename(xlsx_path)
    # LibreOffice 轉換後的檔名預設會是原檔名改副檔名
    ods_filename_no_ext = os.path.splitext(os.path.basename(ods_path))[0]
    expected_output_filename = ods_filename_no_ext + ".xlsx"

    # 使用臨時目錄來進行轉換，避免污染原始目錄
    with tempfile.TemporaryDirectory() as tmpdirname:
        try:
            # 執行 libreoffice 轉換指令
            # --headless: 不啟動圖形介面
            # --convert-to xlsx: 轉換為 xlsx 格式
            # --outdir: 指定輸出目錄
            result = subprocess.run([
                'libreoffice', 
                '--headless', 
                '--convert-to', 'xlsx', 
                ods_path, 
                '--outdir', tmpdirname
            ], capture_output=True, text=True)

            if result.returncode != 0:
                return False

            generated_file_path = os.path.join(tmpdirname, expected_output_filename)
            
            if os.path.exists(generated_file_path):
                # 如果輸出目錄不存在則建立
                if xlsx_dir and not os.path.exists(xlsx_dir):
                    os.makedirs(xlsx_dir)
                
                # 將產生的檔案移動到目標路徑
                shutil.move(generated_file_path, xlsx_path)
                return True
            else:
                return False
        except Exception:
            return False

if __name__ == "__main__":
    # 簡單的測試邏輯（如果直接執行此檔案）
    import sys
    if len(sys.argv) == 3:
        success = convert_ods_to_xlsx(sys.argv[1], sys.argv[2])
        print(f"Conversion {'successful' if success else 'failed'}")
