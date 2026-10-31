"""Regression tests for spreadsheet column filtering at the chunking boundary."""
import importlib
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from openpyxl import Workbook


chunk_module = importlib.import_module("python_packages.index.chunk.get_chunks_from_sheet")


class SheetIncludeFieldsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.file_path = os.path.join(self.temp_dir.name, "items.xlsx")
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "日常用品"
        sheet.append(["品名", "位置", "備註"])
        sheet.append(["西瓜卡", "抽屜", "備用"])
        sheet.append(["充電器", "書桌", "USB-C"])
        workbook.save(self.file_path)

    def get_rows(self, **config):
        config = {"file_path": self.file_path, **config}
        with patch.object(chunk_module, "get_knowledge_base_config", return_value=config):
            chunks = chunk_module.get_chunks_from_sheet("test_goods", "日常用品")
        self.assertIsInstance(chunks, list)
        rows = []
        for chunk in chunks:
            document = json.loads(chunk["document"])
            rows.extend(document if isinstance(document, list) else [document])
        self.assertEqual(len(rows), 2)
        return rows

    def test_legacy_include_fileds(self):
        rows = self.get_rows(include_fileds=["品名"])
        self.assertEqual(rows[0], {"品名": "西瓜卡"})
        self.assertEqual(rows[1], {"品名": "充電器"})

    def test_correctly_spelled_include_fields(self):
        rows = self.get_rows(include_fields="品名, 位置")
        self.assertEqual(rows[0], {"品名": "西瓜卡", "位置": "抽屜"})

    def test_no_filter_includes_all_fields(self):
        rows = self.get_rows()
        self.assertEqual(rows[0], {"品名": "西瓜卡", "位置": "抽屜", "備註": "備用"})


if __name__ == "__main__":
    unittest.main()
