"""HTML 파서 - beautifulsoup4 + markdownify 기반"""

import logging
from pathlib import Path

from doc_to_md.exceptions import ParserError
from doc_to_md.parsers.base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class HtmlParser(BaseParser):
    """HTML 문서를 마크다운으로 변환하는 파서"""

    def supported_extensions(self) -> list[str]:
        return [".html", ".htm"]

    def parse(self, file_path: Path, **kwargs) -> ParseResult:
        """HTML 파일을 마크다운으로 변환"""
        try:
            from bs4 import BeautifulSoup
            import markdownify
        except ImportError:
            raise ParserError(
                "HTML 파싱을 위해 beautifulsoup4와 markdownify를 설치해주세요"
            )

        # 인코딩 자동 감지
        html_content = None
        raw_bytes = file_path.read_bytes()

        # BOM 감지
        if raw_bytes[:2] in (b"\xff\xfe", b"\xfe\xff"):
            try:
                html_content = raw_bytes.decode("utf-16")
            except (UnicodeDecodeError, UnicodeError):
                pass

        if html_content is None:
            for encoding in ["utf-8", "cp949", "euc-kr", "iso-8859-1"]:
                try:
                    html_content = raw_bytes.decode(encoding)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

        if html_content is None:
            html_content = raw_bytes.decode("utf-8", errors="replace")

        soup = BeautifulSoup(html_content, "html.parser")

        # 메타데이터 추출
        metadata = self._extract_metadata(soup)

        # 불필요한 태그 제거
        for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # 본문 영역 우선 추출
        body = soup.find("article") or soup.find("main") or soup.find("body") or soup

        md_content = markdownify.markdownify(
            str(body),
            heading_style="ATX",
            strip=["script", "style"],
        )

        return ParseResult(
            content=md_content.strip(),
            metadata=metadata,
        )

    def _extract_metadata(self, soup) -> dict:
        """HTML 메타데이터 추출"""
        metadata = {}

        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            metadata["title"] = title_tag.string.strip()

        meta_tags = {
            "author": ["author"],
            "description": ["description", "og:description"],
            "keywords": ["keywords"],
        }

        for key, names in meta_tags.items():
            for name in names:
                tag = soup.find("meta", attrs={"name": name}) or \
                      soup.find("meta", attrs={"property": name})
                if tag and tag.get("content"):
                    metadata[key] = tag["content"]
                    break

        return metadata
