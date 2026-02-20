"""BaseParser 추상 클래스 및 ParseResult 데이터 클래스"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParseResult:
    """문서 파싱 결과를 담는 데이터 클래스"""

    content: str
    metadata: dict = field(default_factory=dict)
    images: list[dict] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)


class BaseParser(ABC):
    """모든 문서 파서의 기본 추상 클래스"""

    @abstractmethod
    def parse(self, file_path: Path, **kwargs) -> ParseResult:
        """문서를 파싱하여 ParseResult 반환

        Args:
            file_path: 파싱할 파일 경로
            **kwargs: 파서별 추가 옵션

        Returns:
            ParseResult: 파싱된 결과
        """
        pass

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """지원하는 파일 확장자 목록

        Returns:
            list[str]: 확장자 목록 (예: [".pdf"])
        """
        pass
