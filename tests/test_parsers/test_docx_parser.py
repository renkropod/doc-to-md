"""DOCX 파서 테스트"""

from pathlib import Path

import pytest

from doc_to_md.parsers.docx_parser import DocxParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestDocxParser:
    def setup_method(self):
        self.parser = DocxParser()

    def test_supported_extensions(self):
        exts = self.parser.supported_extensions()
        assert ".docx" in exts
        assert ".doc" in exts

    def test_parse_docx(self):
        docx_path = FIXTURES / "test.docx"
        if not docx_path.exists():
            pytest.skip("테스트 DOCX 파일 없음")

        result = self.parser.parse(docx_path)
        assert result.content
        assert "테스트 DOCX 문서" in result.content
        assert "섹션 2" in result.content

    def test_parse_docx_tables(self):
        docx_path = FIXTURES / "test.docx"
        if not docx_path.exists():
            pytest.skip("테스트 DOCX 파일 없음")

        result = self.parser.parse(docx_path)
        # mammoth 결과에 테이블이 포함되어 있어야 함
        assert "홍길동" in result.content or len(result.tables) > 0
