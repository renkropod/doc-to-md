"""BaseParser 및 ParseResult 테스트"""

from doc_to_md.parsers.base import BaseParser, ParseResult


def test_parse_result_defaults():
    """ParseResult 기본값 테스트"""
    result = ParseResult(content="test")
    assert result.content == "test"
    assert result.metadata == {}
    assert result.images == []
    assert result.tables == []


def test_parse_result_with_data():
    """ParseResult 전체 데이터 테스트"""
    result = ParseResult(
        content="# Hello",
        metadata={"title": "Test"},
        images=[{"path": "img.png", "alt": "img", "page": 1}],
        tables=["| A | B |"],
    )
    assert result.metadata["title"] == "Test"
    assert len(result.images) == 1
    assert len(result.tables) == 1
