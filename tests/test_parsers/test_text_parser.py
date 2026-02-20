"""텍스트 파서 테스트"""

from pathlib import Path

import pytest

from doc_to_md.parsers.text_parser import TextParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestTextParser:
    def setup_method(self):
        self.parser = TextParser()

    def test_supported_extensions(self):
        exts = self.parser.supported_extensions()
        assert ".txt" in exts
        assert ".rtf" in exts

    def test_parse_txt(self):
        txt_path = FIXTURES / "test.txt"
        if not txt_path.exists():
            pytest.skip("테스트 TXT 파일 없음")

        result = self.parser.parse(txt_path)
        assert result.content
        assert "테스트 텍스트" in result.content

    def test_strip_rtf(self):
        rtf = r"{\rtf1\ansi Hello {\b World}}"
        text = TextParser._strip_rtf(rtf)
        assert "Hello" in text
        assert "World" in text
        assert r"\rtf" not in text
