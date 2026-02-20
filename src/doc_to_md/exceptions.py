"""커스텀 예외 클래스"""


class ParserError(Exception):
    """파싱 실패 시 발생하는 예외"""

    pass


class UnsupportedFormatError(Exception):
    """지원하지 않는 파일 포맷에 대한 예외"""

    pass
