from __future__ import annotations  # Убираем ошибки с аннотацией типов
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd


class ExportStrategy(ABC):
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Расширение файла (вместе с точкой)"""
        ...

    @abstractmethod
    def export(self, df: pd.DataFrame, path: Path, encoding: str) -> Path:
        """Сохраняет и Возвращает итоговый путь."""
        ...


class CSVExportStrategy(ExportStrategy):
    """Сохраняет как CSV (разделитель — запятая)"""

    @property
    def file_extension(self) -> str:
        return ".csv"

    def export(self, df: pd.DataFrame, path: Path, encoding: str) -> Path:
        df.to_csv(path, index=False, encoding=encoding)
        return path


class JSONExportStrategy(ExportStrategy):
    """Сохраняет как JSON (читаемый отступ)"""

    @property
    def file_extension(self) -> str:
        return ".json"

    def export(self, df: pd.DataFrame, path: Path, encoding: str) -> Path:
        df.to_json(path, orient="records", force_ascii=False, indent=2)
        return path
