def parse_knowledge_id(knowledge_id):
    if "!" in knowledge_id:
        parts = knowledge_id.rsplit("!", 1)
        knowledge_id = parts[0]
        section_name = parts[1]
    else:
        knowledge_id = knowledge_id
        section_name = None
    
    return {
        "knowledge_id": knowledge_id,
        "section_name": section_name,
    }

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "my_knowledge_base!Sheet1",
        "another_kb",
        "kb_with_multiple!exclamations!Sheet2",
        "!Sheet3",
        "no_sheet_name!",
        "",
    ]

    for case in test_cases:
        result = parse_knowledge_id(case)
        print(f"Input: '{case}' -> Output: {result}")
