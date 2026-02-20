"""파일 타입 감지 테스트"""

from pathlib import Path

import pytest

from doc_to_md.utils.file_detect import detect_file_type, _detect_by_extension

FIXTURES = Path(__file__).parent / "fixtures"


class TestFileDetect:
    def test_detect_by_extension_pdf(self):
        assert _detect_by_extension(Path("test.pdf")) == "pdf"

    def test_detect_by_extension_docx(self):
        assert _detect_by_extension(Path("test.docx")) == "docx"

    def test_detect_by_extension_hwp(self):
        assert _detect_by_extension(Path("test.hwp")) == "hwp"

    def test_detect_by_extension_xlsx(self):
        assert _detect_by_extension(Path("test.xlsx")) == "xlsx"

    def test_detect_by_extension_html(self):
        assert _detect_by_extension(Path("test.html")) == "html"

    def test_detect_by_extension_unknown(self):
        assert _detect_by_extension(Path("test.xyz")) is None

    def test_detect_file_type_real_file(self):
        pdf_path = FIXTURES / "test.pdf"
        if not pdf_path.exists():
            pytest.skip("테스트 PDF 없음")
        assert detect_file_type(pdf_path) == "pdf"

    def test_detect_unsupported(self):
        with pytest.raises(ValueError, match="지원하지 않는"):
            detect_file_type(Path("/tmp/test.xyz"))
