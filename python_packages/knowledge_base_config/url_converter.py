from python_packages.knowledge_base_config.convert.convert_file_to_md import convert_file_to_md
from python_packages.knowledge_base_config.convert.convert_google_sheets_url_to_ods_download import convert_google_sheets_url_to_ods_download
from python_packages.knowledge_base_config.convert.convert_google_doc_url_to_md_download import convert_google_doc_url_to_md_download
from python_packages.knowledge_base_config.convert.convert_google_slide_url_to_md_download import convert_google_slide_url_to_md_download

if __name__ == '__main__':
    # Example usage for local file
    test_file_path = "/path/to/your/local/file.txt"
    converted_file_path = convert_file_to_md(test_file_path)
    print(f"Original file path: {test_file_path}")
    print(f"Converted file path (md): {converted_file_path}")
    print("-" * 30)

    # Example usage for Google Sheets
    test_url_sheets_edit = "https://docs.google.com/spreadsheets/d/1RB4kKW0s5eUH6f2t3f7m6qnd3OGGbXp0fzQ3zEYn_rM/edit?usp=sharing"
    test_url_sheets_other = "https://www.example.com/document"
    test_url_sheets_no_usp = "https://docs.google.com/spreadsheets/d/1RB4kKW0s5eUH6f2t3f7m6qnd3OGGbXp0fzQ3zEYn_rM/edit"

    converted_url_sheets_edit = convert_google_sheets_url_to_ods_download(test_url_sheets_edit)
    converted_url_sheets_other = convert_google_sheets_url_to_ods_download(test_url_sheets_other)
    converted_url_sheets_no_usp = convert_google_sheets_url_to_ods_download(test_url_sheets_no_usp)

    print(f"Original (Sheets edit): {test_url_sheets_edit}")
    print(f"Converted (Sheets ods): {converted_url_sheets_edit}")
    print("-" * 30)
    print(f"Original (Sheets other): {test_url_sheets_other}")
    print(f"Converted (Sheets other): {converted_url_sheets_other}")
    print("-" * 30)
    print(f"Original (Sheets no usp): {test_url_sheets_no_usp}")
    print(f"Converted (Sheets no usp): {converted_url_sheets_no_usp}")
    print("-" * 30)

    # Example usage for Google Docs
    test_url_doc_edit = "https://docs.google.com/document/d/12345abcde/edit?usp=sharing"
    test_url_doc_view = "https://docs.google.com/document/d/12345abcde/view"
    test_url_doc_other = "https://www.example.com/document"

    converted_url_doc_edit = convert_google_doc_url_to_md_download(test_url_doc_edit)
    converted_url_doc_view = convert_google_doc_url_to_md_download(test_url_doc_view)
    converted_url_doc_other = convert_google_doc_url_to_md_download(test_url_doc_other)

    print(f"Original (Doc edit): {test_url_doc_edit}")
    print(f"Converted (Doc md): {converted_url_doc_edit}")
    print("-" * 30)
    print(f"Original (Doc view): {test_url_doc_view}")
    print(f"Converted (Doc md): {converted_url_doc_view}")
    print("-" * 30)
    print(f"Original (Doc other): {test_url_doc_other}")
    print(f"Converted (Doc other): {converted_url_doc_other}")
    print("-" * 30)

    # Example usage for Google Slides
    test_url_slide_edit = "https://docs.google.com/presentation/d/67890fghij/edit?usp=sharing"
    test_url_slide_view = "https://docs.google.com/presentation/d/67890fghij/view"
    test_url_slide_other = "https://www.example.com/presentation"

    converted_url_slide_edit = convert_google_slide_url_to_md_download(test_url_slide_edit)
    converted_url_slide_view = convert_google_slide_url_to_md_download(test_url_slide_view)
    converted_url_slide_other = convert_google_slide_url_to_md_download(test_url_slide_other)

    print(f"Original (Slide edit): {test_url_slide_edit}")
    print(f"Converted (Slide md): {converted_url_slide_edit}")
    print("-" * 30)
    print(f"Original (Slide view): {test_url_slide_view}")
    print(f"Converted (Slide md): {converted_url_slide_view}")
    print("-" * 30)
    print(f"Original (Slide other): {test_url_slide_other}")
    print(f"Converted (Slide other): {converted_url_slide_other}")
