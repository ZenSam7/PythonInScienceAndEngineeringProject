import pandas as pd
from typing import Callable, Iterable, Iterator, Any
import pathlib
from data_processing import Config


class TripIterator:
    """
    Файл открывается при создании, закрывается по StopIteration или __del__
    """

    def __init__(self, config: Config, filepath: pathlib.Path):
        # О существовании filepath уже позаботились в TripIterable
        self._file = open(filepath, encoding=config.encoding, newline="")
        self._csv_separator = ","
        self._headers = self._file.readline().strip().split(self._csv_separator)  # csv импоритровать не хочу
        self.config = config

    def __iter__(self) -> "TripIterator":
        return self

    def __next__(self) -> dict:
        try:
            return self._cast(
                dict(
                    zip(
                        self._headers,
                        self._file.readline().strip().split(self._csv_separator),
                    )
                )
            )
        except StopIteration:
            self._file.close()
            raise

    def _cast(self, row: dict) -> dict:
        """Приводим строки CSV к нужным типам — DictReader всё отдаёт str"""
        for field, field_type in self.config.COLUMNS_TYPE.items():
            row[field] = self.config.CONVERT_FUNCS[field_type](row[field])
        return row

    def __del__(self):
        # На случай если итерацию прервали break-ом — файл не завис
        if hasattr(self, "_file") and not self._file.closed:
            self._file.close()


# Итерируемый объект
class TripIterable:
    """
    Хранит только путь
    Каждый __iter__() открывает файл заново → можно итерироваться несколько раз.
    """

    def __init__(self, config: Config):
        self._filepath = config.output_path / config.cleaned_file_name
        if not self._filepath.exists():
            raise FileNotFoundError(f"Файл не найден: {filepath}")
        self.config = config

    def __iter__(self) -> TripIterator:
        return TripIterator(
            self.config, self._filepath
        )  # свежий файловый дескриптор каждый раз


class FilterIterator:
    """
    Пропускает только строки, где filter(row) == True
    """

    def __init__(self, iterable: Iterable, filter: Callable[[dict], bool]):
        self._iterator = iter(iterable)  # один раз создаём итератор
        self._filter = filter

    def __iter__(self) -> "FilterIterator":
        return self

    def __next__(self) -> dict:
        while True:
            row = next(self._iterator)  # пробрасывает StopIteration сам
            if self._filter(row):
                return row


class MapIterator:
    """
    Применяет transform к каждому элементу по требованию
    """

    def __init__(self, iterable: Iterable, transform: Callable[[dict], Any]):
        self._iterator = iter(iterable)
        self._transform = transform

    def __iter__(self) -> "MapIterator":
        return self

    def __next__(self) -> Any:
        return self._transform(next(self._iterator))
