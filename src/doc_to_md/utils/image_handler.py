"""이미지 추출 및 저장 유틸리티"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def save_image(
    image_data: bytes,
    output_dir: Path,
    filename: str,
) -> Path:
    """이미지 데이터를 파일로 저장

    Args:
        image_data: 이미지 바이너리 데이터
        output_dir: 이미지 저장 디렉토리
        filename: 저장할 파일명

    Returns:
        Path: 저장된 이미지 파일 경로
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / filename
    image_path.write_bytes(image_data)
    logger.debug("이미지 저장: %s", image_path)
    return image_path


def generate_image_filename(
    base_name: str,
    index: int,
    extension: str = ".png",
) -> str:
    """이미지 파일명 생성

    Args:
        base_name: 원본 문서 파일명 (확장자 제외)
        index: 이미지 인덱스
        extension: 이미지 확장자

    Returns:
        str: 생성된 파일명
    """
    if not extension.startswith("."):
        extension = f".{extension}"
    return f"{base_name}_img_{index:03d}{extension}"


def get_image_dir(output_path: Path) -> Path:
    """출력 파일 경로에 기반한 이미지 디렉토리 경로 반환

    Args:
        output_path: 출력 마크다운 파일 경로

    Returns:
        Path: 이미지 저장 디렉토리 경로
    """
    return output_path.parent / f"{output_path.stem}_images"
