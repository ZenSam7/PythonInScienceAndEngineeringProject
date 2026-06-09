"""
Тесты для iterators.py.

Покрывают:
  - FilterIterator: ленивая фильтрация
  - MapIterator: ленивое преобразование
  - TripIterator._cast: DataValidationError на плохих данных
  - TripIterable: FileNotFoundError при отсутствии файла
"""
import pathlib

import pytest

from iterators import FilterIterator, MapIterator, TripIterable, TripIterator
from errors import DataValidationError
from data_processing import Config

pytestmark = pytest.mark.streaming  # ← кастомная mark для всего модуля


# ══════════════════════════════════════════════════════════════════════════════
# FilterIterator
# ══════════════════════════════════════════════════════════════════════════════
class TestFilterIterator:
    def test_filters_correctly(self):
        """Должны пройти только элементы с hour >= 8"""
        data = [{"hour": h, "val": h * 10} for h in range(24)]
        result = list(FilterIterator(data, lambda r: r["hour"] >= 8))
        assert all(r["hour"] >= 8 for r in result)
        assert len(result) == 16   # 8..23 включительно

    def test_empty_source(self):
        """Пустой источник → пустой результат"""
        result = list(FilterIterator([], lambda r: True))
        assert result == []

    def test_no_match(self):
        """Если ни одна строка не проходит фильтр → пустой список"""
        data = [{"x": 1}, {"x": 2}]
        result = list(FilterIterator(data, lambda r: r["x"] > 100))
        assert result == []

    @pytest.mark.parametrize("threshold,expected_count", [
        (0,  5),   # все 5 строк
        (2,  3),   # x = 2,3,4
        (4,  1),   # только x = 4
        (10, 0),   # ничего
    ])
    def test_parametrized_threshold(self, threshold, expected_count):
        """Проверяем разные пороги через parametrize"""
        data = [{"x": i} for i in range(5)]
        result = list(FilterIterator(data, lambda r: r["x"] >= threshold))
        assert len(result) == expected_count


# ══════════════════════════════════════════════════════════════════════════════
# MapIterator
# ══════════════════════════════════════════════════════════════════════════════
class TestMapIterator:
    def test_transforms_values(self):
        """MapIterator должен применить transform к каждому элементу"""
        data = [{"pay": 10.0}, {"pay": 20.0}]
        result = list(MapIterator(data, lambda r: r["pay"] * 2))
        assert result == [20.0, 40.0]

    def test_chaining_with_filter(self):
        """FilterIterator + MapIterator должны работать в связке лениво"""
        data = [{"hour": h, "pay": float(h)} for h in range(24)]
        pays = list(
            MapIterator(
                FilterIterator(data, lambda r: 6 <= r["hour"] <= 10),
                lambda r: r["pay"],
            )
        )
        assert pays == [6.0, 7.0, 8.0, 9.0, 10.0]

    def test_empty_source(self):
        result = list(MapIterator([], lambda r: r))
        assert result == []


# ══════════════════════════════════════════════════════════════════════════════
# TripIterator._cast: DataValidationError
# ══════════════════════════════════════════════════════════════════════════════
class TestTripIteratorCast:
    @pytest.fixture
    def iterator_with_header(self, tmp_path, config):
        """Создаём TripIterator из CSV-файла, содержащего только заголовок"""
        csv_path = tmp_path / "header_only.csv"
        headers = list(config.COLUMNS_TYPE.keys())
        csv_path.write_text(",".join(headers) + "\n", encoding=config.encoding)
        return TripIterator(config, csv_path)

    def test_data_validation_error_on_bad_float(self, iterator_with_header, config):
        """_cast должен поднять DataValidationError если float-поле содержит строку"""
        bad_row = {k: "invalid_value" for k in config.COLUMNS_TYPE}
        with pytest.raises(DataValidationError) as exc_info:
            iterator_with_header._cast(bad_row)
        # Проверяем что исключение несёт информацию о поле
        assert exc_info.value.field is not None

    def test_data_validation_error_has_field_info(self, iterator_with_header, config):
        """DataValidationError должен содержать имя проблемного поля"""
        bad_row = {k: "???" for k in config.COLUMNS_TYPE}
        try:
            iterator_with_header._cast(bad_row)
        except DataValidationError as e:
            assert e.field in config.COLUMNS_TYPE
        else:
            pytest.fail("DataValidationError не был поднят")


# ══════════════════════════════════════════════════════════════════════════════
# TripIterable: FileNotFoundError
# ══════════════════════════════════════════════════════════════════════════════
class TestTripIterable:
    def test_raises_file_not_found(self, config, tmp_path):
        """TripIterable должен поднять FileNotFoundError если файл не существует"""
        cfg = Config()
        cfg.output_dir = str(tmp_path)   # пустая папка
        with pytest.raises(FileNotFoundError):
            TripIterable(cfg)
