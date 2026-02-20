"""CLI 엔트리포인트"""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from doc_to_md.converter import convert_batch, convert_file

app = typer.Typer(
    name="doc-to-md",
    help="다양한 문서 포맷을 Markdown(.md) 파일로 변환합니다.",
    add_completion=False,
)
console = Console()


def _setup_logging(verbose: bool) -> None:
    """로깅 설정"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@app.command()
def convert(
    input_file: Path = typer.Argument(..., help="변환할 입력 파일 경로"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="출력 마크다운 파일 경로"
    ),
    extract_images: bool = typer.Option(
        False, "--extract-images", help="이미지를 별도 폴더에 저장"
    ),
    image_dir: Optional[Path] = typer.Option(
        None, "--image-dir", help="이미지 저장 경로"
    ),
    ocr: bool = typer.Option(False, "--ocr", help="OCR 활성화 (스캔 PDF 등)"),
    ocr_lang: str = typer.Option(
        "kor+eng", "--ocr-lang", help="OCR 언어 설정"
    ),
    no_metadata: bool = typer.Option(
        False, "--no-metadata", help="메타데이터 헤더 제외"
    ),
    clean: bool = typer.Option(False, "--clean", help="후처리 정리 활성화"),
    encoding: str = typer.Option("utf-8", "--encoding", help="출력 인코딩"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="디버그 로그 활성화"),
) -> None:
    """단일 파일을 마크다운으로 변환합니다."""
    _setup_logging(verbose)

    try:
        result_path = convert_file(
            input_path=input_file,
            output_path=output,
            extract_images=extract_images,
            image_dir=image_dir,
            ocr=ocr,
            ocr_lang=ocr_lang,
            no_metadata=no_metadata,
            clean=clean,
            encoding=encoding,
        )
        console.print(f"[green]변환 완료:[/green] {result_path}")
    except FileNotFoundError as e:
        console.print(f"[red]오류:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]변환 실패:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., help="입력 디렉토리 경로"),
    output_dir: Path = typer.Option(
        "./output", "--output", "-o", help="출력 디렉토리 경로"
    ),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="하위 디렉토리 포함"
    ),
    extract_images: bool = typer.Option(
        False, "--extract-images", help="이미지를 별도 폴더에 저장"
    ),
    ocr: bool = typer.Option(False, "--ocr", help="OCR 활성화"),
    ocr_lang: str = typer.Option("kor+eng", "--ocr-lang", help="OCR 언어 설정"),
    no_metadata: bool = typer.Option(
        False, "--no-metadata", help="메타데이터 헤더 제외"
    ),
    clean: bool = typer.Option(False, "--clean", help="후처리 정리 활성화"),
    encoding: str = typer.Option("utf-8", "--encoding", help="출력 인코딩"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="디버그 로그 활성화"),
) -> None:
    """디렉토리 내 파일을 일괄 변환합니다."""
    _setup_logging(verbose)

    if not input_dir.is_dir():
        console.print(f"[red]오류:[/red] 디렉토리가 아닙니다: {input_dir}")
        raise typer.Exit(code=1)

    results = convert_batch(
        input_dir=input_dir,
        output_dir=output_dir,
        recursive=recursive,
        extract_images=extract_images,
        ocr=ocr,
        ocr_lang=ocr_lang,
        no_metadata=no_metadata,
        clean=clean,
        encoding=encoding,
    )

    table = Table(title="변환 결과")
    table.add_column("파일", style="cyan")
    table.add_column("상태", style="bold")
    table.add_column("출력/오류")

    success_count = 0
    fail_count = 0

    for r in results:
        if r["status"] == "success":
            success_count += 1
            table.add_row(
                Path(r["file"]).name,
                "[green]성공[/green]",
                str(r["output"]),
            )
        else:
            fail_count += 1
            table.add_row(
                Path(r["file"]).name,
                "[red]실패[/red]",
                r.get("error", "알 수 없는 오류"),
            )

    console.print(table)
    console.print(
        f"\n총 {len(results)}개 파일: "
        f"[green]{success_count}개 성공[/green], "
        f"[red]{fail_count}개 실패[/red]"
    )


if __name__ == "__main__":
    app()
