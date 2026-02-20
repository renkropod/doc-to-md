"""XLSX/CSV 파서 테스트"""

from pathlib import Path

import pytest

from doc_to_md.parsers.xlsx_parser import XlsxParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestXlsxParser:
    def setup_method(self):
        self.parser = XlsxParser()

    def test_supported_extensions(self):
        exts = self.parser.supported_extensions()
        assert ".xlsx" in exts
        assert ".csv" in exts

    def test_parse_xlsx(self):
        xlsx_path = FIXTURES / "test.xlsx"
        if not xlsx_path.exists():
            pytest.skip("테스트 XLSX 파일 없음")

        result = self.parser.parse(xlsx_path)
        assert result.content
        assert "김철수" in result.content
        assert "직원목록" in result.content

    def test_rows_to_markdown(self):
        rows = [["A", "B"], ["1", "2"]]
        md = XlsxParser._rows_to_markdown(rows)
        assert "| A | B |" in md
        assert "| 1 | 2 |" in md

    def test_rows_to_markdown_empty(self):
        assert XlsxParser._rows_to_markdown([]) == ""
