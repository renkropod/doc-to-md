"""텍스트/RTF 파서 - 내장 파서"""

import logging
from pathlib import Path

from doc_to_md.parsers.base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class TextParser(BaseParser):
    """TXT/RTF 파일을 마크다운으로 변환하는 파서"""

    def supported_extensions(self) -> list[str]:
        return [".txt", ".rtf", ".md", ".text"]

    def parse(self, file_path: Path, **kwargs) -> ParseResult:
        """텍스트 파일을 읽어 마크다운으로 변환"""
        content = None

        # 인코딩 자동 감지
        for encoding in ["utf-8", "utf-8-sig", "cp949", "euc-kr", "iso-8859-1"]:
            try:
                content = file_path.read_text(encoding=encoding)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if content is None:
            content = file_path.read_bytes().decode("utf-8", errors="replace")

        suffix = file_path.suffix.lower()
        if suffix == ".rtf":
            content = self._strip_rtf(content)

        metadata = {
            "source": file_path.name,
        }

        return ParseResult(
            content=content.strip(),
            metadata=metadata,
        )

    @staticmethod
    def _strip_rtf(content: str) -> str:
        """RTF 포맷에서 순수 텍스트 추출 (간이 파서)"""
        import re

        # RTF 제어 단어 제거
        content = re.sub(r"\\[a-z]+\d*\s?", "", content)
        # 중괄호 제거
        content = re.sub(r"[{}]", "", content)
        # 특수 RTF 시퀀스 처리
        content = content.replace("\\par", "\n")
        content = content.replace("\\tab", "\t")
        content = content.replace("\\\\", "\\")
        content = content.replace("\\{", "{")
        content = content.replace("\\}", "}")
        return content.strip()
