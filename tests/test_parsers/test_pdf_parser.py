"""PDF 파서 테스트"""

from pathlib import Path

import pytest

from doc_to_md.parsers.pdf_parser import PdfParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestPdfParser:
    def setup_method(self):
        self.parser = PdfParser()

    def test_supported_extensions(self):
        assert ".pdf" in self.parser.supported_extensions()

    def test_parse_pdf(self):
        pdf_path = FIXTURES / "test.pdf"
        if not pdf_path.exists():
            pytest.skip("테스트 PDF 파일 없음")

        result = self.parser.parse(pdf_path)
        assert result.content
        assert isinstance(result.metadata, dict)

    def test_table_to_markdown(self):
        table = [["이름", "나이"], ["홍길동", "30"], ["김철수", "25"]]
        md = PdfParser._table_to_markdown(table)
        assert "| 이름 | 나이 |" in md
        assert "| --- | --- |" in md
        assert "| 홍길동 | 30 |" in md

    def test_table_to_markdown_empty(self):
        assert PdfParser._table_to_markdown([]) == ""
        assert PdfParser._table_to_markdown([[]]) == ""
