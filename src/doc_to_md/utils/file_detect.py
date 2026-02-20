"""파일 타입 자동 감지 모듈"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

EXTENSION_TO_TYPE: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".hwp": "hwp",
    ".hwpx": "hwpx",
    ".pptx": "pptx",
    ".ppt": "pptx",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".csv": "csv",
    ".html": "html",
    ".htm": "html",
    ".epub": "epub",
    ".txt": "text",
    ".rtf": "text",
    ".md": "text",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".tiff": "image",
    ".tif": "image",
    ".bmp": "image",
    ".gif": "image",
    ".webp": "image",
}

MIME_TO_TYPE: dict[str, str] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "docx",
    "application/x-hwp": "hwp",
    "application/haansofthwp": "hwp",
    "application/vnd.hancom.hwpx": "hwpx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/vnd.ms-powerpoint": "pptx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-excel": "xlsx",
    "text/csv": "csv",
    "text/html": "html",
    "application/epub+zip": "epub",
    "text/plain": "text",
    "text/rtf": "text",
    "application/rtf": "text",
    "image/png": "image",
    "image/jpeg": "image",
    "image/tiff": "image",
    "image/bmp": "image",
    "image/gif": "image",
    "image/webp": "image",
}


def detect_file_type(file_path: Path) -> str:
    """파일 타입을 자동 감지

    python-magic(libmagic)으로 MIME 타입 기반 감지를 시도하고,
    실패 시 확장자 기반 감지를 fallback으로 사용합니다.

    Args:
        file_path: 감지할 파일 경로

    Returns:
        str: 파일 타입 문자열 (예: "pdf", "docx", "hwp")

    Raises:
        ValueError: 지원하지 않는 파일 타입
    """
    ext_type = _detect_by_extension(file_path)

    mime_type = _detect_by_magic(file_path)

    if mime_type and ext_type:
        if mime_type != ext_type:
            logger.warning(
                "파일 확장자(%s→%s)와 실제 타입(%s)이 다릅니다. "
                "실제 타입을 사용합니다.",
                file_path.suffix,
                ext_type,
                mime_type,
            )
        return mime_type

    result = mime_type or ext_type
    if result:
        return result

    raise ValueError(
        f"지원하지 않는 파일 형식입니다: {file_path.suffix} "
        f"(파일: {file_path.name})"
    )


def _detect_by_extension(file_path: Path) -> str | None:
    """확장자 기반 파일 타입 감지"""
    ext = file_path.suffix.lower()
    return EXTENSION_TO_TYPE.get(ext)


def _detect_by_magic(file_path: Path) -> str | None:
    """python-magic을 사용한 MIME 타입 기반 파일 타입 감지"""
    try:
        import magic

        mime = magic.from_file(str(file_path), mime=True)
        return MIME_TO_TYPE.get(mime)
    except ImportError:
        logger.debug("python-magic이 설치되지 않았습니다. 확장자 기반 감지를 사용합니다.")
        return None
    except Exception as e:
        logger.debug("magic 감지 실패: %s", e)
        return None
