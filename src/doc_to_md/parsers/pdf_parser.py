"""PDF 파서 - pymupdf4llm 1순위, pdfplumber fallback"""

import logging
from pathlib import Path

from doc_to_md.exceptions import ParserError
from doc_to_md.parsers.base import BaseParser, ParseResult
from doc_to_md.utils.image_handler import generate_image_filename, save_image

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    """PDF 문서를 마크다운으로 변환하는 파서"""

    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def parse(self, file_path: Path, **kwargs) -> ParseResult:
        """PDF 파일을 파싱하여 마크다운으로 변환

        pymupdf4llm을 1순위로 시도하고, 실패 시 pdfplumber로 fallback합니다.
        """
        extract_images = kwargs.get("extract_images", False)
        image_dir = kwargs.get("image_dir")
        ocr = kwargs.get("ocr", False)

        try:
            return self._parse_with_pymupdf4llm(
                file_path, extract_images, image_dir
            )
        except Exception as e:
            logger.warning("pymupdf4llm 파싱 실패, pdfplumber로 fallback: %s", e)

        try:
            return self._parse_with_pdfplumber(
                file_path, extract_images, image_dir
            )
        except Exception as e:
            logger.warning("pdfplumber 파싱 실패: %s", e)

        if ocr:
            try:
                return self._parse_with_ocr(file_path, kwargs.get("ocr_lang", "kor+eng"))
            except Exception as e:
                logger.warning("OCR 파싱 실패: %s", e)

        raise ParserError(f"PDF 파싱 실패: {file_path}")

    def _parse_with_pymupdf4llm(
        self,
        file_path: Path,
        extract_images: bool,
        image_dir: Path | None,
    ) -> ParseResult:
        """pymupdf4llm을 사용한 PDF 파싱"""
        import pymupdf4llm
        import pymupdf

        md_text = pymupdf4llm.to_markdown(str(file_path))

        doc = pymupdf.open(str(file_path))
        metadata = self._extract_metadata(doc)
        images: list[dict] = []

        if extract_images and image_dir:
            images = self._extract_images_pymupdf(doc, image_dir, file_path.stem)

        doc.close()

        return ParseResult(
            content=md_text,
            metadata=metadata,
            images=images,
        )

    def _parse_with_pdfplumber(
        self,
        file_path: Path,
        extract_images: bool,
        image_dir: Path | None,
    ) -> ParseResult:
        """pdfplumber를 사용한 PDF 파싱"""
        import pdfplumber

        parts: list[str] = []
        tables: list[str] = []
        metadata = {}

        with pdfplumber.open(str(file_path)) as pdf:
            if pdf.metadata:
                metadata = {
                    k: str(v) for k, v in pdf.metadata.items() if v
                }

            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    parts.append(text)

                for table in page.extract_tables():
                    md_table = self._table_to_markdown(table)
                    tables.append(md_table)
                    parts.append(md_table)

                if i < len(pdf.pages) - 1:
                    parts.append("\n---\n")

        return ParseResult(
            content="\n\n".join(parts),
            metadata=metadata,
            tables=tables,
        )

    def _parse_with_ocr(self, file_path: Path, ocr_lang: str) -> ParseResult:
        """OCR을 사용한 스캔 PDF 파싱"""
        import pymupdf
        from PIL import Image
        import pytesseract
        import io

        doc = pymupdf.open(str(file_path))
        parts: list[str] = []
        metadata = self._extract_metadata(doc)

        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang=ocr_lang)
            if text.strip():
                parts.append(text.strip())

        doc.close()

        return ParseResult(
            content="\n\n".join(parts),
            metadata=metadata,
        )

    def _extract_metadata(self, doc) -> dict:
        """PyMuPDF 문서에서 메타데이터 추출"""
        meta = doc.metadata or {}
        return {k: str(v) for k, v in meta.items() if v}

    def _extract_images_pymupdf(
        self,
        doc,
        image_dir: Path,
        base_name: str,
    ) -> list[dict]:
        """PyMuPDF를 사용하여 이미지 추출"""
        images: list[dict] = []
        img_index = 0

        for page_num, page in enumerate(doc):
            for img_ref in page.get_images(full=True):
                xref = img_ref[0]
                try:
                    base_image = doc.extract_image(xref)
                    if base_image:
                        ext = base_image.get("ext", "png")
                        filename = generate_image_filename(
                            base_name, img_index, ext
                        )
                        save_image(base_image["image"], image_dir, filename)
                        images.append({
                            "path": str(image_dir / filename),
                            "alt": f"Image {img_index}",
                            "page": page_num + 1,
                        })
                        img_index += 1
                except Exception as e:
                    logger.debug("이미지 추출 실패 (xref=%d): %s", xref, e)

        return images

    @staticmethod
    def _table_to_markdown(table: list[list]) -> str:
        """2D 리스트를 마크다운 테이블로 변환"""
        if not table or not table[0]:
            return ""

        def cell_str(cell) -> str:
            return str(cell).strip().replace("|", "\\|") if cell else ""

        header = table[0]
        col_count = len(header)
        lines = [
            "| " + " | ".join(cell_str(c) for c in header) + " |",
            "| " + " | ".join("---" for _ in range(col_count)) + " |",
        ]

        for row in table[1:]:
            padded = list(row) + [""] * (col_count - len(row))
            lines.append(
                "| " + " | ".join(cell_str(c) for c in padded[:col_count]) + " |"
            )

        return "\n".join(lines)
