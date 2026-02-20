# doc-to-md

다양한 문서 포맷(PDF, DOCX, HWP, PPTX, XLSX, HTML, EPUB 등)을 Markdown(.md) 파일로 변환하는 Python CLI 도구

## 지원 포맷

| 포맷 | 확장자 | 라이브러리 |
|------|--------|-----------|
| PDF | `.pdf` | pymupdf4llm, pdfplumber |
| DOCX | `.docx`, `.doc` | mammoth, python-docx |
| HWP/HWPX | `.hwp`, `.hwpx` | olefile (커스텀 바이너리 파서) |
| PPTX | `.pptx`, `.ppt` | python-pptx |
| XLSX/CSV | `.xlsx`, `.xls`, `.csv` | openpyxl, pandas |
| HTML | `.html`, `.htm` | beautifulsoup4, markdownify |
| EPUB | `.epub` | ebooklib |
| 이미지 | `.png`, `.jpg`, `.tiff` 등 | pytesseract (OCR) |
| 텍스트 | `.txt`, `.rtf` | 내장 파서 |

## 설치

```bash
# 기본 설치
pip install -e .

# 전체 파서 설치
pip install -e ".[all]"

# 특정 파서만 설치
pip install -e ".[pdf]"
pip install -e ".[docx]"
pip install -e ".[hwp]"
pip install -e ".[ocr]"
```

## 사용법

### 단일 파일 변환

```bash
doc-to-md convert input.pdf -o output.md
doc-to-md convert input.docx -o output.md --extract-images --image-dir ./images/
doc-to-md convert input.hwp -o output.md --clean
```

### 디렉토리 일괄 변환

```bash
doc-to-md batch ./documents/ -o ./output/ --recursive
```

### 옵션

| 옵션 | 설명 |
|------|------|
| `--output`, `-o` | 출력 파일/디렉토리 경로 |
| `--extract-images` | 이미지를 별도 폴더에 저장 |
| `--image-dir` | 이미지 저장 경로 |
| `--ocr` | OCR 활성화 (스캔 PDF, 이미지) |
| `--ocr-lang` | OCR 언어 설정 (기본: `kor+eng`) |
| `--no-metadata` | 메타데이터 헤더 제외 |
| `--clean` | 후처리 정리 활성화 |
| `--encoding` | 출력 인코딩 (기본: `utf-8`) |
| `--verbose`, `-v` | 디버그 로그 활성화 |

## 테스트

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## 프로젝트 구조

```
doc-to-md/
├── pyproject.toml
├── README.md
├── src/doc_to_md/
│   ├── cli.py              # CLI 엔트리포인트 (typer)
│   ├── converter.py         # 메인 변환 오케스트레이터
│   ├── exceptions.py        # 커스텀 예외
│   ├── parsers/
│   │   ├── base.py          # BaseParser 추상 클래스
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── hwp_parser.py
│   │   ├── pptx_parser.py
│   │   ├── xlsx_parser.py
│   │   ├── html_parser.py
│   │   ├── epub_parser.py
│   │   ├── image_parser.py
│   │   └── text_parser.py
│   ├── postprocess/
│   │   ├── cleaner.py       # MD 정리/정규화
│   │   └── formatter.py     # 헤딩/리스트 포맷팅
│   └── utils/
│       ├── file_detect.py   # 파일 타입 자동 감지
│       └── image_handler.py # 이미지 추출/저장
├── tests/
└── output/
```
