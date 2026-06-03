import pandas as pd
from typing import Callable, Iterable, Iterator, Any


class TripIterator:
    """
    Знает текущую позицию, умеет отдать следующую строку
    """

    def __init__(self, records: list[dict]):
        self._records = records
        self._index = 0

    def __iter__(self) -> "TripIterator":
        return self  # итератор возвращает сам себя

    def __next__(self) -> dict:
        if self._index >= len(self._records):
            raise StopIteration
        value = self._records[self._index]
        self._index += 1
        return value

    def __len__(self) -> int:
        return len(self._records)


# Итерируемый объект
class TripIterable:
    """
    Хранит данные, но сам не итератор, а фабрика итераторов
    """

    def __init__(self, df: pd.DataFrame):
        self._records: list[dict] = df.to_dict("records")

    def __iter__(self) -> TripIterator:
        return TripIterator(self._records)  # каждый раз новый

    def __len__(self) -> int:
        return len(self._records)


class FilterIterator:
    """
    Пропускает только строки, где predicate(row) == True
    """

    def __init__(self, iterable, predicate: Callable[[dict], bool]):
        self._iterator = iter(iterable)  # один раз создаём итератор
        self._predicate = predicate

    def __iter__(self) -> "FilterIterator":
        return self

    def __next__(self) -> dict:
        while True:
            row = next(self._iterator)  # пробрасывает StopIteration сам
            if self._predicate(row):
                return row


class MapIterator:
    """
    Применяет transform к каждому элементу по требованию
    """

    def __init__(self, iterable, transform: Callable[[dict], Any]):
        self._iterator = iter(iterable)
        self._transform = transform

    def __iter__(self) -> "MapIterator":
        return self

    def __next__(self) -> Any:
        return self._transform(next(self._iterator))
