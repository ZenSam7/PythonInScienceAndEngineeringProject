from __future__ import annotations  # Убираем ошибки с аннотацией типов

import datetime
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd
import json


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

    @abstractmethod
    def import_file(self, path: Path, encoding: str) -> pd.DataFrame:
        """Также отвечаем и за импорт"""
        ...

    def readline(self, file: IO) -> dict:
        """Читаем файл из нужного формата ровно 1 строчку данных. возвращаем словарь"""
        ...


class CSVExportStrategy(ExportStrategy):
    """Сохраняет как CSV (разделитель — запятая)"""
    _headers = None
    _csv_separator = ","

    @property
    def file_extension(self) -> str:
        return ".csv"

    def export(self, df: pd.DataFrame, path: Path, encoding: str) -> Path:
        df.to_csv(path, index=False, encoding=encoding)
        return path

    def import_file(self, path: Path, encoding: str) -> pd.DataFrame:
        return pd.read_csv(path, encoding=encoding)

    def readline(self, file: IO) -> dict:
        # csv импоритровать не хочу
        if not self._headers:
            read_headers = lambda: file.readline().strip().split(self._csv_separator)

            if file.tell() == 0:
                self._headers = read_headers()
            else:
                last_tell = file.tell()
                file.seek(0)
                self._headers = read_headers()
                file.seek(last_tell)

        line = file.readline()
        if not line:
            return None

        row = dict(zip(self._headers, line.strip().split(self._csv_separator)))
        return row


class JSONExportStrategy(ExportStrategy):
    """Сохраняет как JSON (читаемый отступ)"""
    _json_data = None
    _current_index = 0

    @property
    def file_extension(self) -> str:
        return ".json"

    def export(self, df: pd.DataFrame, path: Path, encoding: str) -> Path:
        df.to_json(path, orient="records", force_ascii=False, indent=2, date_format="iso")
        return path

    def import_file(self, path: Path, encoding: str) -> pd.DataFrame:
        return pd.read_json(path, encoding=encoding)

    def readline(self, file: IO) -> dict:
        buffer = []
        in_object = False

        for line in file:
            stripped = line.strip()

            # Нашли начало объекта
            if stripped.startswith("{"):
                in_object = True
                buffer.append(line)
                continue

            if in_object:
                buffer.append(line)

                # Нашли конец объекта (учитываем возможную запятую после скобки)
                if stripped.startswith("}") or stripped.startswith("},"):
                    # Убираем возможную висящую запятую в конце объекта для корректного json.loads
                    obj_str = "".join(buffer).rstrip().rstrip(",")

                    return json.loads(obj_str)
