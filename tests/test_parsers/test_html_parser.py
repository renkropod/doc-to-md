"""HTML 파서 테스트"""

from pathlib import Path

import pytest

from doc_to_md.parsers.html_parser import HtmlParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestHtmlParser:
    def setup_method(self):
        self.parser = HtmlParser()

    def test_supported_extensions(self):
        exts = self.parser.supported_extensions()
        assert ".html" in exts
        assert ".htm" in exts

    def test_parse_html(self):
        html_path = FIXTURES / "test.html"
        if not html_path.exists():
            pytest.skip("테스트 HTML 파일 없음")

        result = self.parser.parse(html_path)
        assert result.content
        assert "HTML 테스트 문서" in result.content
        assert result.metadata.get("title") == "테스트 HTML"
        assert result.metadata.get("author") == "테스터"
