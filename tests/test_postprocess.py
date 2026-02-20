"""후처리 모듈 테스트"""

from doc_to_md.postprocess.cleaner import clean_markdown
from doc_to_md.postprocess.formatter import format_markdown


class TestCleaner:
    def test_collapse_blank_lines(self):
        text = "a\n\n\n\n\n\nb"
        result = clean_markdown(text)
        assert result.count("\n") <= 3

    def test_fix_broken_encoding(self):
        text = "hello\ufffdworld\x00test"
        result = clean_markdown(text)
        assert "\ufffd" not in result
        assert "\x00" not in result

    def test_strip_trailing_whitespace(self):
        text = "hello   \nworld  \n"
        result = clean_markdown(text)
        assert "   " not in result.split("\n")[0]


class TestFormatter:
    def test_normalize_headings(self):
        text = "#Hello\n##World"
        result = format_markdown(text)
        assert "# Hello" in result
        assert "## World" in result

    def test_normalize_list_markers(self):
        text = "* item1\n+ item2\n- item3"
        result = format_markdown(text)
        assert result.count("- ") == 3
        assert "* " not in result
        assert "+ " not in result
