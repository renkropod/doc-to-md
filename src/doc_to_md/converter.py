"""메인 변환 오케스트레이터"""

import logging
from pathlib import Path

from doc_to_md.exceptions import ParserError, UnsupportedFormatError
from doc_to_md.parsers.base import BaseParser, ParseResult
from doc_to_md.utils.file_detect import detect_file_type

logger = logging.getLogger(__name__)

# 파일 타입 → 파서 클래스 매핑 (지연 로딩)
_PARSER_REGISTRY: dict[str, type[BaseParser]] = {}


def register_parser(file_type: str, parser_class: type[BaseParser]) -> None:
    """파서를 레지스트리에 등록

    Args:
        file_type: 파일 타입 문자열 (예: "pdf")
        parser_class: 파서 클래스
    """
    _PARSER_REGISTRY[file_type] = parser_class


def get_parser(file_type: str) -> BaseParser:
    """파일 타입에 해당하는 파서 인스턴스를 반환

    Args:
        file_type: 파일 타입 문자열

    Returns:
        BaseParser: 파서 인스턴스

    Raises:
        UnsupportedFormatError: 해당 파일 타입의 파서가 없는 경우
    """
    _ensure_parsers_loaded()
    parser_class = _PARSER_REGISTRY.get(file_type)
    if parser_class is None:
        raise UnsupportedFormatError(
            f"'{file_type}' 타입을 처리할 파서가 없습니다. "
            f"지원 타입: {list(_PARSER_REGISTRY.keys())}"
        )
    return parser_class()


def convert_file(
    input_path: Path,
    output_path: Path | None = None,
    extract_images: bool = False,
    image_dir: Path | None = None,
    ocr: bool = False,
    ocr_lang: str = "kor+eng",
    no_metadata: bool = False,
    clean: bool = False,
    encoding: str = "utf-8",
) -> Path:
    """단일 파일을 마크다운으로 변환

    Args:
        input_path: 입력 파일 경로
        output_path: 출력 파일 경로 (None이면 자동 생성)
        extract_images: 이미지 추출 여부
        image_dir: 이미지 저장 디렉토리
        ocr: OCR 활성화 여부
        ocr_lang: OCR 언어 설정
        no_metadata: 메타데이터 헤더 제외 여부
        clean: 후처리 정리 활성화 여부
        encoding: 출력 인코딩

    Returns:
        Path: 생성된 마크다운 파일 경로

    Raises:
        FileNotFoundError: 입력 파일이 없는 경우
        ParserError: 파싱 실패
        UnsupportedFormatError: 지원하지 않는 파일 형식
    """
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {input_path}")

    if output_path is None:
        output_path = input_path.with_suffix(".md")
    output_path = Path(output_path).resolve()

    file_type = detect_file_type(input_path)
    logger.info("파일 타입 감지: %s → %s", input_path.name, file_type)

    parser = get_parser(file_type)
    logger.info("파서 사용: %s", parser.__class__.__name__)

    result: ParseResult = parser.parse(
        input_path,
        extract_images=extract_images,
        image_dir=image_dir or _default_image_dir(output_path),
        ocr=ocr,
        ocr_lang=ocr_lang,
    )

    content = _build_output(result, no_metadata=no_metadata)

    if clean:
        from doc_to_md.postprocess.cleaner import clean_markdown
        from doc_to_md.postprocess.formatter import format_markdown

        content = clean_markdown(content)
        content = format_markdown(content)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding=encoding)
    logger.info("변환 완료: %s", output_path)

    return output_path


def convert_batch(
    input_dir: Path,
    output_dir: Path,
    recursive: bool = False,
    **kwargs,
) -> list[dict]:
    """디렉토리 내 파일을 일괄 변환

    Args:
        input_dir: 입력 디렉토리
        output_dir: 출력 디렉토리
        recursive: 하위 디렉토리 포함 여부
        **kwargs: convert_file에 전달할 추가 옵션

    Returns:
        list[dict]: 변환 결과 리포트 리스트
    """
    input_dir = Path(input_dir).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    pattern = "**/*" if recursive else "*"
    results = []

    for file_path in sorted(input_dir.glob(pattern)):
        if not file_path.is_file():
            continue

        try:
            detect_file_type(file_path)
        except ValueError:
            continue

        relative = file_path.relative_to(input_dir)
        out_path = output_dir / relative.with_suffix(".md")

        try:
            convert_file(file_path, out_path, **kwargs)
            results.append({
                "file": str(file_path),
                "output": str(out_path),
                "status": "success",
            })
        except Exception as e:
            logger.error("변환 실패: %s - %s", file_path, e)
            results.append({
                "file": str(file_path),
                "output": None,
                "status": "failed",
                "error": str(e),
            })

    return results


def _build_output(result: ParseResult, no_metadata: bool = False) -> str:
    """ParseResult를 최종 마크다운 문자열로 조합"""
    parts: list[str] = []

    if not no_metadata and result.metadata:
        parts.append("---")
        for key, value in result.metadata.items():
            parts.append(f"{key}: {value}")
        parts.append("---")
        parts.append("")

    parts.append(result.content)

    return "\n".join(parts)


def _default_image_dir(output_path: Path) -> Path:
    """출력 경로 기반 기본 이미지 디렉토리"""
    return output_path.parent / f"{output_path.stem}_images"


def _ensure_parsers_loaded() -> None:
    """파서들을 레지스트리에 등록 (지연 로딩)"""
    if _PARSER_REGISTRY:
        return

    _try_register("doc_to_md.parsers.pdf_parser", "PdfParser")
    _try_register("doc_to_md.parsers.docx_parser", "DocxParser")
    _try_register("doc_to_md.parsers.hwp_parser", "HwpParser")
    _try_register("doc_to_md.parsers.pptx_parser", "PptxParser")
    _try_register("doc_to_md.parsers.xlsx_parser", "XlsxParser")
    _try_register("doc_to_md.parsers.html_parser", "HtmlParser")
    _try_register("doc_to_md.parsers.epub_parser", "EpubParser")
    _try_register("doc_to_md.parsers.image_parser", "ImageParser")
    _try_register("doc_to_md.parsers.text_parser", "TextParser")


def _try_register(module_name: str, class_name: str) -> None:
    """모듈에서 파서 클래스를 동적으로 로드하여 등록"""
    try:
        import importlib

        module = importlib.import_module(module_name)
        parser_class = getattr(module, class_name)
        instance = parser_class()
        for ext in instance.supported_extensions():
            file_type = ext.lstrip(".")
            register_parser(file_type, parser_class)
    except (ImportError, AttributeError) as e:
        logger.debug("파서 로드 건너뜀: %s.%s - %s", module_name, class_name, e)
