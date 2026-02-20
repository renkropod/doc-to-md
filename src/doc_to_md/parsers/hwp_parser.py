"""HWP/HWPX 파서 - olefile 기반 HWP + ZIP 기반 HWPX"""

import io
import logging
import struct
import zipfile
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

from doc_to_md.exceptions import ParserError
from doc_to_md.parsers.base import BaseParser, ParseResult
from doc_to_md.utils.image_handler import generate_image_filename, save_image

logger = logging.getLogger(__name__)


class HwpParser(BaseParser):
    """HWP/HWPX 문서를 마크다운으로 변환하는 파서"""

    def supported_extensions(self) -> list[str]:
        return [".hwp", ".hwpx"]

    def parse(self, file_path: Path, **kwargs) -> ParseResult:
        """HWP/HWPX 파일을 파싱"""
        extract_images = kwargs.get("extract_images", False)
        image_dir = kwargs.get("image_dir")

        suffix = file_path.suffix.lower()

        if suffix == ".hwpx":
            return self._parse_hwpx(file_path, extract_images, image_dir)
        elif suffix == ".hwp":
            return self._parse_hwp(file_path, extract_images, image_dir)
        else:
            raise ParserError(f"지원하지 않는 HWP 확장자: {suffix}")

    def _parse_hwpx(
        self,
        file_path: Path,
        extract_images: bool,
        image_dir: Path | None,
    ) -> ParseResult:
        """HWPX (XML 기반) 파싱 - ZIP 해제 후 XML 파싱"""
        parts: list[str] = []
        images: list[dict] = []
        tables: list[str] = []
        metadata: dict = {}
        img_index = 0

        try:
            with zipfile.ZipFile(str(file_path), "r") as zf:
                # 메타데이터 읽기
                metadata = self._read_hwpx_metadata(zf)

                # 본문 섹션 파일 찾기
                section_files = sorted([
                    name for name in zf.namelist()
                    if name.startswith("Contents/section") and name.endswith(".xml")
                ])

                if not section_files:
                    # 대안 경로 시도
                    section_files = sorted([
                        name for name in zf.namelist()
                        if "section" in name.lower() and name.endswith(".xml")
                    ])

                for section_file in section_files:
                    xml_data = zf.read(section_file)
                    section_text, section_tables = self._parse_hwpx_section(xml_data)
                    if section_text:
                        parts.append(section_text)
                    tables.extend(section_tables)

                # 이미지 추출
                if extract_images and image_dir:
                    for name in zf.namelist():
                        if self._is_image_file(name):
                            try:
                                img_data = zf.read(name)
                                ext = Path(name).suffix or ".png"
                                filename = generate_image_filename(
                                    file_path.stem, img_index, ext
                                )
                                save_image(img_data, image_dir, filename)
                                images.append({
                                    "path": str(image_dir / filename),
                                    "alt": f"Image {img_index}",
                                    "page": 0,
                                })
                                img_index += 1
                            except Exception as e:
                                logger.debug("HWPX 이미지 추출 실패: %s", e)

        except zipfile.BadZipFile as e:
            raise ParserError(f"HWPX 파일이 올바르지 않습니다: {e}") from e

        if not parts:
            raise ParserError(f"HWPX에서 텍스트를 추출할 수 없습니다: {file_path}")

        return ParseResult(
            content="\n\n".join(parts),
            metadata=metadata,
            images=images,
            tables=tables,
        )

    def _parse_hwpx_section(self, xml_data: bytes) -> tuple[str, list[str]]:
        """HWPX 섹션 XML 파싱"""
        parts: list[str] = []
        tables: list[str] = []

        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            logger.warning("HWPX XML 파싱 실패: %s", e)
            return "", []

        # 네임스페이스 처리
        ns = {}
        for prefix, uri in [
            ("hp", "http://www.hancom.co.kr/hwpml/2011/paragraph"),
            ("ht", "http://www.hancom.co.kr/hwpml/2011/text"),
            ("hc", "http://www.hancom.co.kr/hwpml/2011/core"),
        ]:
            ns[prefix] = uri

        # 모든 텍스트 노드에서 텍스트 추출
        self._extract_text_recursive(root, parts, tables, ns)

        return "\n\n".join(parts), tables

    def _extract_text_recursive(
        self,
        element: ET.Element,
        parts: list[str],
        tables: list[str],
        ns: dict,
    ) -> None:
        """재귀적으로 XML 요소에서 텍스트 추출"""
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

        # 텍스트 노드
        if element.text and element.text.strip():
            text = element.text.strip()
            parts.append(text)

        # 자식 요소 재귀 탐색
        for child in element:
            self._extract_text_recursive(child, parts, tables, ns)

        # tail 텍스트
        if element.tail and element.tail.strip():
            parts.append(element.tail.strip())

    def _read_hwpx_metadata(self, zf: zipfile.ZipFile) -> dict:
        """HWPX 메타데이터 읽기"""
        metadata = {}
        try:
            if "META-INF/container.xml" in zf.namelist():
                pass  # 컨테이너 정보

            # content.hpf에서 메타데이터 읽기
            for name in zf.namelist():
                if name.lower().endswith(".hpf") or "meta" in name.lower():
                    try:
                        xml_data = zf.read(name)
                        root = ET.fromstring(xml_data)
                        for child in root.iter():
                            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                            if tag in ("title", "creator", "subject", "description"):
                                if child.text:
                                    metadata[tag] = child.text
                    except Exception:
                        continue
        except Exception as e:
            logger.debug("HWPX 메타데이터 읽기 실패: %s", e)

        return metadata

    def _parse_hwp(
        self,
        file_path: Path,
        extract_images: bool,
        image_dir: Path | None,
    ) -> ParseResult:
        """HWP (바이너리) 파싱 - olefile 기반"""
        try:
            import olefile
        except ImportError:
            raise ParserError(
                "HWP 파싱을 위해 olefile을 설치해주세요: pip install olefile"
            )

        if not olefile.isOleFile(str(file_path)):
            raise ParserError(f"올바른 HWP 파일이 아닙니다: {file_path}")

        ole = olefile.OleFileIO(str(file_path))
        parts: list[str] = []
        images: list[dict] = []
        metadata: dict = {}
        img_index = 0

        try:
            # 파일 헤더 읽기
            header = ole.openstream("FileHeader").read()
            is_compressed = bool(header[36] & 1)

            # 본문 텍스트 추출
            section_idx = 0
            while True:
                stream_name = f"BodyText/Section{section_idx}"
                if not ole.exists(stream_name):
                    break

                data = ole.openstream(stream_name).read()

                if is_compressed:
                    try:
                        data = zlib.decompress(data, -15)
                    except zlib.error:
                        logger.debug("섹션 %d 압축 해제 실패", section_idx)
                        section_idx += 1
                        continue

                text = self._extract_hwp_text(data)
                if text:
                    parts.append(text)

                section_idx += 1

            # 메타데이터
            metadata = self._read_hwp_metadata(ole)

            # 이미지 추출
            if extract_images and image_dir:
                for stream in ole.listdir():
                    stream_path = "/".join(stream)
                    if stream_path.startswith("BinData/"):
                        try:
                            img_data = ole.openstream(stream_path).read()
                            if is_compressed:
                                try:
                                    img_data = zlib.decompress(img_data, -15)
                                except zlib.error:
                                    pass

                            ext = self._guess_image_ext(img_data)
                            filename = generate_image_filename(
                                file_path.stem, img_index, ext
                            )
                            save_image(img_data, image_dir, filename)
                            images.append({
                                "path": str(image_dir / filename),
                                "alt": f"Image {img_index}",
                                "page": 0,
                            })
                            img_index += 1
                        except Exception as e:
                            logger.debug("HWP 이미지 추출 실패: %s", e)

        finally:
            ole.close()

        if not parts:
            raise ParserError(f"HWP에서 텍스트를 추출할 수 없습니다: {file_path}")

        return ParseResult(
            content="\n\n".join(parts),
            metadata=metadata,
            images=images,
        )

    def _extract_hwp_text(self, data: bytes) -> str:
        """HWP 바이너리 섹션 데이터에서 텍스트 추출"""
        text_parts: list[str] = []
        i = 0

        while i < len(data):
            if i + 4 > len(data):
                break

            # 레코드 헤더 읽기 (4바이트)
            header = struct.unpack_from("<I", data, i)[0]
            tag_id = header & 0x3FF
            level = (header >> 10) & 0x3FF
            size = (header >> 20) & 0xFFF

            if size == 0xFFF:
                if i + 8 > len(data):
                    break
                size = struct.unpack_from("<I", data, i + 4)[0]
                i += 8
            else:
                i += 4

            if i + size > len(data):
                break

            record_data = data[i : i + size]
            i += size

            # HWPTAG_PARA_TEXT = 67
            if tag_id == 67:
                text = self._decode_para_text(record_data)
                if text.strip():
                    text_parts.append(text.strip())

        return "\n\n".join(text_parts)

    def _decode_para_text(self, data: bytes) -> str:
        """HWP 문단 텍스트 디코딩"""
        chars: list[str] = []
        i = 0

        while i + 1 < len(data):
            code = struct.unpack_from("<H", data, i)[0]
            i += 2

            if code == 0:
                break
            elif code < 32:
                # 제어 문자 건너뛰기
                if code in (1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23):
                    # 인라인/확장 제어 문자는 추가 데이터가 있음
                    i += 14 if code <= 3 else 14
                elif code == 10:
                    chars.append("\n")
                elif code == 13:
                    chars.append("\n")
                elif code == 24:
                    pass  # 하이픈
                elif code == 30:
                    chars.append("\u00A0")  # Non-breaking space
            else:
                chars.append(chr(code))

        return "".join(chars)

    def _read_hwp_metadata(self, ole) -> dict:
        """HWP OLE 파일에서 메타데이터 읽기"""
        metadata = {}
        try:
            meta = ole.get_metadata()
            if meta.title:
                metadata["title"] = meta.title
            if meta.author:
                metadata["author"] = meta.author
            if meta.subject:
                metadata["subject"] = meta.subject
            if meta.creating_application:
                metadata["application"] = meta.creating_application
        except Exception as e:
            logger.debug("HWP 메타데이터 읽기 실패: %s", e)
        return metadata

    @staticmethod
    def _is_image_file(name: str) -> bool:
        """파일 이름이 이미지인지 판별"""
        img_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".wmf", ".emf"}
        return Path(name).suffix.lower() in img_extensions

    @staticmethod
    def _guess_image_ext(data: bytes) -> str:
        """바이너리 데이터의 매직 바이트로 이미지 확장자 추측"""
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "png"
        elif data[:2] == b"\xff\xd8":
            return "jpg"
        elif data[:4] == b"GIF8":
            return "gif"
        elif data[:2] == b"BM":
            return "bmp"
        elif data[:4] == b"II\x2a\x00" or data[:4] == b"MM\x00\x2a":
            return "tiff"
        return "png"
