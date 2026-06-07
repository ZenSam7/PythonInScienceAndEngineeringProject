import pathlib
from typing import Callable, Iterable, Iterator, Any
from data_processing import Config
from exceptions import DataValidationError


class TripIterator:
    """
    Файл открывается при создании, закрывается по StopIteration или __del__
    При каждой строке вызывает _cast() и может бросить DataValidationError
    """

    def __init__(self, config: Config, filepath: pathlib.Path):
        self._file = open(filepath, encoding=config.encoding, newline="")
        self._csv_separator = ","
        self._headers = self._file.readline().strip().split(self._csv_separator)  # csv импоритровать не хочу
        self.config = config

    def __iter__(self) -> "TripIterator":
        return self

    def __next__(self) -> dict:
        line = self._file.readline()
        if not line:          # EOF — файл закрываем сами
            self._file.close()
            raise StopIteration
        row = dict(zip(self._headers, line.strip().split(self._csv_separator)))
        return self._cast(row)

    def _cast(self, row: dict) -> dict or DataValidationError:
        """
        Приводим строки CSV к нужным типам
        """
        for field, field_type in self.config.COLUMNS_TYPE.items():
            try:
                row[field] = self.config.CONVERT_FUNCS[field_type](row[field])
            except (ValueError, KeyError, TypeError) as exc:
                raise DataValidationError(
                    f"Не удалось привести значение к типу {field_type.__name__}",
                    field=field,
                    value=row.get(field),
                ) from exc
        return row

    def __del__(self):
        # На случай если итерацию прервали break-ом — файл не завис
        if hasattr(self, "_file") and not self._file.closed:
            self._file.close()


# ── итерируемый объект ────────────────────────────────────────────────────────
class TripIterable:
    """
    Хранит только путь к файлу
    Каждый __iter__() открывает файл заново
    """

    def __init__(self, config: Config):
        self._filepath = config.output_path / config.cleaned_file_name
        if not self._filepath.exists():
            raise FileNotFoundError(f"Файл не найден: {self._filepath}")
        self.config = config

    def __iter__(self) -> TripIterator:
        # свежий файловый дескриптор каждый раз
        return TripIterator(self.config, self._filepath)


# ─────────────────────────────────────────────────────────────
class FilterIterator:
    """Пропускает только строки, где filter_fn(row) == True"""

    def __init__(self, iterable: Iterable, filter_func: Callable[[dict], bool]):
        self._iterator = iter(iterable)
        self._filter = filter_func

    def __iter__(self) -> "FilterIterator":
        return self

    def __next__(self) -> dict:
        while True:
            row = next(self._iterator)   # сам пробросит StopIteration
            if self._filter(row):
                return row


# ───────────────────────────────────────────────────
class MapIterator:
    """Применяет transform к каждому элементу по требованию"""

    def __init__(self, iterable: Iterable, transform: Callable[[dict], Any]):
        self._iterator = iter(iterable)
        self._transform = transform

    def __iter__(self) -> "MapIterator":
        return self

    def __next__(self) -> Any:
        return self._transform(next(self._iterator))
