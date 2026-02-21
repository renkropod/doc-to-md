"""FastAPI Web UI 앱"""

import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from doc_to_md.converter import convert_file
from doc_to_md.exceptions import ParserError, UnsupportedFormatError

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="doc-to-md", description="문서 → Markdown 변환 웹 UI")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

SUPPORTED_FORMATS = [
    {"ext": ".pdf", "name": "PDF"},
    {"ext": ".docx / .doc", "name": "Word"},
    {"ext": ".hwp / .hwpx", "name": "한글"},
    {"ext": ".pptx", "name": "PowerPoint"},
    {"ext": ".xlsx / .csv", "name": "Excel / CSV"},
    {"ext": ".html", "name": "HTML"},
    {"ext": ".epub", "name": "EPUB"},
    {"ext": ".png / .jpg", "name": "이미지 (OCR)"},
    {"ext": ".txt / .rtf", "name": "텍스트"},
]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """메인 페이지"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "formats": SUPPORTED_FORMATS},
    )


@app.post("/convert")
async def convert_document(
    file: UploadFile = File(...),
    clean: bool = Form(False),
    no_metadata: bool = Form(False),
    ocr: bool = Form(False),
    ocr_lang: str = Form("kor+eng"),
):
    """파일 업로드 → 변환 → .md 파일 다운로드"""
    tmp_dir = tempfile.mkdtemp()
    try:
        input_path = Path(tmp_dir) / file.filename
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        output_path = input_path.with_suffix(".md")

        convert_file(
            input_path=input_path,
            output_path=output_path,
            clean=clean,
            no_metadata=no_metadata,
            ocr=ocr,
            ocr_lang=ocr_lang,
        )

        return FileResponse(
            path=str(output_path),
            filename=output_path.name,
            media_type="text/markdown; charset=utf-8",
            background=_cleanup_task(tmp_dir),
        )
    except (ParserError, UnsupportedFormatError) as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return JSONResponse(
            status_code=422,
            content={"error": str(e)},
        )
    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"변환 실패: {e}"},
        )


@app.post("/convert/preview")
async def convert_preview(
    file: UploadFile = File(...),
    clean: bool = Form(False),
    no_metadata: bool = Form(False),
    ocr: bool = Form(False),
    ocr_lang: str = Form("kor+eng"),
):
    """파일 업로드 → 변환 → JSON 미리보기 응답"""
    tmp_dir = tempfile.mkdtemp()
    try:
        input_path = Path(tmp_dir) / file.filename
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        output_path = input_path.with_suffix(".md")

        convert_file(
            input_path=input_path,
            output_path=output_path,
            clean=clean,
            no_metadata=no_metadata,
            ocr=ocr,
            ocr_lang=ocr_lang,
        )

        content = output_path.read_text(encoding="utf-8")

        return JSONResponse(content={
            "filename": output_path.name,
            "content": content,
            "size": len(content),
        })
    except (ParserError, UnsupportedFormatError) as e:
        return JSONResponse(
            status_code=422,
            content={"error": str(e)},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"변환 실패: {e}"},
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _cleanup_task(tmp_dir: str):
    """BackgroundTask로 임시 디렉토리 정리"""
    from starlette.background import BackgroundTask

    return BackgroundTask(shutil.rmtree, tmp_dir, True)
