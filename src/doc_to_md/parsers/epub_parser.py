"""EPUB 파서 - ebooklib 기반"""

import logging
from pathlib import Path

from doc_to_md.exceptions import ParserError
from doc_to_md.parsers.base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class EpubParser(BaseParser):
    """EPUB 전자책을 마크다운으로 변환하는 파서"""

    def supported_extensions(self) -> list[str]:
        return [".epub"]

    def parse(self, file_path: Path, **kwargs) -> ParseResult:
        """EPUB 파일을 마크다운으로 변환"""
        extract_images = kwargs.get("extract_images", False)
        image_dir = kwargs.get("image_dir")

        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            import markdownify
        except ImportError:
            raise ParserError(
                "EPUB 파싱을 위해 ebooklib, beautifulsoup4, markdownify를 설치해주세요"
            )

        try:
            book = epub.read_epub(str(file_path))
        except Exception as e:
            raise ParserError(f"EPUB 파일 열기 실패: {e}") from e

        parts: list[str] = []
        images: list[dict] = []
        metadata = self._extract_metadata(book)

        # 문서 항목 순서대로 처리
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            html_content = item.get_content().decode("utf-8", errors="replace")
            soup = BeautifulSoup(html_content, "html.parser")

            # 불필요한 태그 제거
            for tag in soup.find_all(["script", "style"]):
                tag.decompose()

            body = soup.find("body") or soup

            md_content = markdownify.markdownify(
                str(body),
                heading_style="ATX",
                strip=["script", "style"],
            )

            text = md_content.strip()
            if text:
                parts.append(text)

        # 이미지 추출
        if extract_images and image_dir:
            from doc_to_md.utils.image_handler import generate_image_filename, save_image
            img_index = 0

            for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                try:
                    filename = generate_image_filename(
                        file_path.stem, img_index, Path(item.file_name).suffix or ".png"
                    )
                    save_image(item.get_content(), image_dir, filename)
                    images.append({
                        "path": str(image_dir / filename),
                        "alt": f"Image {img_index}",
                        "page": 0,
                    })
                    img_index += 1
                except Exception as e:
                    logger.debug("EPUB 이미지 추출 실패: %s", e)

        return ParseResult(
            content="\n\n---\n\n".join(parts),
            metadata=metadata,
            images=images,
        )

    def _extract_metadata(self, book) -> dict:
        """EPUB 메타데이터 추출"""
        metadata = {}
        try:
            title = book.get_metadata("DC", "title")
            if title:
                metadata["title"] = title[0][0]
            creator = book.get_metadata("DC", "creator")
            if creator:
                metadata["author"] = creator[0][0]
            language = book.get_metadata("DC", "language")
            if language:
                metadata["language"] = language[0][0]
            description = book.get_metadata("DC", "description")
            if description:
                metadata["description"] = description[0][0]
        except Exception as e:
            logger.debug("EPUB 메타데이터 추출 실패: %s", e)
        return metadata
