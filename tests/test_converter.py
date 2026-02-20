"""Converter 통합 테스트"""

from pathlib import Path

import pytest

from doc_to_md.converter import convert_file, _build_output
from doc_to_md.exceptions import UnsupportedFormatError
from doc_to_md.parsers.base import ParseResult

FIXTURES = Path(__file__).parent / "fixtures"
OUTPUT = Path(__file__).parent.parent / "output" / "test_results"


class TestConverter:
    def test_convert_pdf(self, tmp_path):
        pdf_path = FIXTURES / "test.pdf"
        if not pdf_path.exists():
            pytest.skip("테스트 PDF 없음")

        out = tmp_path / "result.md"
        result = convert_file(pdf_path, out)
        assert result.exists()
        assert result.read_text().strip()

    def test_convert_docx(self, tmp_path):
        docx_path = FIXTURES / "test.docx"
        if not docx_path.exists():
            pytest.skip("테스트 DOCX 없음")

        out = tmp_path / "result.md"
        result = convert_file(docx_path, out)
        assert result.exists()
        content = result.read_text()
        assert "테스트 DOCX 문서" in content

    def test_convert_html(self, tmp_path):
        html_path = FIXTURES / "test.html"
        if not html_path.exists():
            pytest.skip("테스트 HTML 없음")

        out = tmp_path / "result.md"
        result = convert_file(html_path, out)
        assert result.exists()

    def test_convert_txt(self, tmp_path):
        txt_path = FIXTURES / "test.txt"
        if not txt_path.exists():
            pytest.skip("테스트 TXT 없음")

        out = tmp_path / "result.md"
        result = convert_file(txt_path, out)
        assert result.exists()

    def test_convert_xlsx(self, tmp_path):
        xlsx_path = FIXTURES / "test.xlsx"
        if not xlsx_path.exists():
            pytest.skip("테스트 XLSX 없음")

        out = tmp_path / "result.md"
        result = convert_file(xlsx_path, out)
        assert result.exists()

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            convert_file(Path("/nonexistent/file.pdf"), tmp_path / "out.md")

    def test_build_output_with_metadata(self):
        result = ParseResult(
            content="# Hello",
            metadata={"title": "Test", "author": "Kim"},
        )
        output = _build_output(result)
        assert "---" in output
        assert "title: Test" in output
        assert "# Hello" in output

    def test_build_output_no_metadata(self):
        result = ParseResult(content="# Hello", metadata={"title": "Test"})
        output = _build_output(result, no_metadata=True)
        assert "---" not in output
        assert "# Hello" in output
