"""마크다운 포맷팅 모듈 - 헤딩 레벨 조정, 링크 처리 등"""

import re


def format_markdown(content: str) -> str:
    """마크다운 포맷 정규화

    Args:
        content: 원본 마크다운 텍스트

    Returns:
        str: 포맷 정규화된 마크다운 텍스트
    """
    content = _normalize_headings(content)
    content = _ensure_heading_spacing(content)
    content = _normalize_list_markers(content)
    return content


def _normalize_headings(content: str) -> str:
    """헤딩 레벨 정규화 - # 뒤에 공백이 없으면 추가"""
    return re.sub(r"^(#{1,6})([^ #\n])", r"\1 \2", content, flags=re.MULTILINE)


def _ensure_heading_spacing(content: str) -> str:
    """헤딩 앞뒤에 빈 줄 보장"""
    lines = content.split("\n")
    result: list[str] = []

    for i, line in enumerate(lines):
        is_heading = bool(re.match(r"^#{1,6}\s", line))

        if is_heading and result and result[-1].strip() != "":
            result.append("")

        result.append(line)

        if is_heading and i + 1 < len(lines) and lines[i + 1].strip() != "":
            result.append("")

    return "\n".join(result)


def _normalize_list_markers(content: str) -> str:
    """리스트 마커 정규화 (*, +, - → -)"""
    return re.sub(r"^(\s*)[*+]\s", r"\1- ", content, flags=re.MULTILINE)
