"""마크다운 정리/정규화 모듈"""

import re


def clean_markdown(content: str) -> str:
    """마크다운 텍스트를 정리

    Args:
        content: 원본 마크다운 텍스트

    Returns:
        str: 정리된 마크다운 텍스트
    """
    content = _collapse_blank_lines(content)
    content = _fix_broken_encoding(content)
    content = _strip_trailing_whitespace(content)
    return content


def _collapse_blank_lines(content: str) -> str:
    """연속 빈 줄을 최대 2줄로 제한"""
    return re.sub(r"\n{4,}", "\n\n\n", content)


def _fix_broken_encoding(content: str) -> str:
    """깨진 문자/인코딩 복구 시도"""
    replacements = {
        "\ufffd": "",
        "\x00": "",
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    return content


def _strip_trailing_whitespace(content: str) -> str:
    """각 줄의 끝 공백 제거"""
    lines = content.split("\n")
    return "\n".join(line.rstrip() for line in lines)
