
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.draw import Frame, Image
from odf.text import P
import base64
import zipfile
import io

def get_text(cell):
    text_content = []
    for p in cell.getElementsByType(P):
        text_content.append(str(p))
    return "\n".join(text_content)

def explore_ods(filepath):
    doc = load(filepath)
    zf = zipfile.ZipFile(filepath)
    
    for sheet in doc.spreadsheet.getElementsByType(Table):
        sheet_name = sheet.getAttribute('name')
        print(f"Sheet: {sheet_name}")
        
        rows = sheet.getElementsByType(TableRow)
        if rows:
            row = rows[0]
            cells = row.getElementsByType(TableCell)
            current_col = 1
            for cell in cells:
                repeat_cols = int(cell.getAttribute('numbercolumnsrepeated') or 1)
                text = get_text(cell)
                print(f"  Col {current_col} (x{repeat_cols}): '{text}'")
                current_col += repeat_cols

if __name__ == "__main__":
    explore_ods('knowledge_base_files/shopping_cart.ods')
