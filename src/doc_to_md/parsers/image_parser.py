"""이미지 파서 - OCR 기반 텍스트 추출"""

import logging
from pathlib import Path

from doc_to_md.exceptions import ParserError
from doc_to_md.parsers.base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class ImageParser(BaseParser):
    """이미지에서 OCR로 텍스트를 추출하는 파서"""

    def supported_extensions(self) -> list[str]:
        return [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"]

    def parse(self, file_path: Path, **kwargs) -> ParseResult:
        """이미지 파일에서 OCR로 텍스트 추출"""
        ocr_lang = kwargs.get("ocr_lang", "kor+eng")

        try:
            from PIL import Image
            import pytesseract
        except ImportError:
            raise ParserError(
                "이미지 OCR을 위해 pytesseract와 Pillow를 설치해주세요: "
                "pip install pytesseract Pillow"
            )

        try:
            img = Image.open(str(file_path))
        except Exception as e:
            raise ParserError(f"이미지 파일 열기 실패: {e}") from e

        try:
            text = pytesseract.image_to_string(img, lang=ocr_lang)
        except Exception as e:
            raise ParserError(
                f"OCR 실패: {e}. tesseract가 설치되어 있는지 확인해주세요."
            ) from e

        metadata = {
            "source": file_path.name,
            "format": img.format or file_path.suffix.lstrip(".").upper(),
            "size": f"{img.width}x{img.height}",
        }

        return ParseResult(
            content=text.strip(),
            metadata=metadata,
        )
