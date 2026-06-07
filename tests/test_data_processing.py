import pathlib

import pandas as pd
import pytest

from data_processing import Config, DataCleaner, DataLoader, DataExporter, EmptyDatasetError
from errors import EmptyDatasetError
from strategies import CSVExportStrategy, JSONExportStrategy

pytestmark = pytest.mark.processing  # ← кастомная mark для всего модуля


# ══════════════════════════════════════════════════════════════════════════════
# Шаг 1: удаление нулевых поездок
# ══════════════════════════════════════════════════════════════════════════════
class TestStep1DropZeroTrips:
    def test_removes_zero_row(self, config, raw_df):
        """Строка с нулями (index=2) должна исчезнуть."""
        cleaner = DataCleaner(config, raw_df)
        cleaner.step1_drop_zero_trips()
        assert len(cleaner.df) == 2

    def test_valid_rows_survive(self, config, raw_df):
        """Валидные строки не должны быть удалены."""
        cleaner = DataCleaner(config, raw_df)
        cleaner.step1_drop_zero_trips()
        assert (cleaner.df["driver_pay"] != 0).all()
        assert (cleaner.df["trip_miles"] != 0).all()

    @pytest.mark.parametrize("col", ["trip_miles", "trip_time", "driver_pay"])
    def test_zero_in_any_column_drops_row(self, config, raw_df, col):
        """Ноль в *любой* из трёх ключевых колонок должен удалять строку."""
        raw_df = raw_df.copy()
        raw_df.loc[0, col] = 0.0          # портим первую (валидную) строку
        cleaner = DataCleaner(config, raw_df)
        cleaner.step1_drop_zero_trips()
        assert 0.0 not in cleaner.df[col].values


# ══════════════════════════════════════════════════════════════════════════════
# Шаг 2: удаление строк с NaT
# ══════════════════════════════════════════════════════════════════════════════
class TestStep2DropNullDatetimes:
    def test_removes_nat_row(self, config, raw_df):
        """Строка с NaT в pickup_datetime должна исчезнуть."""
        raw_df = raw_df.copy()
        raw_df.loc[0, "pickup_datetime"] = pd.NaT
        before = len(raw_df)
        cleaner = DataCleaner(config, raw_df)
        cleaner.step2_drop_null_datetimes()
        assert len(cleaner.df) == before - 1

    def test_valid_datetimes_survive(self, config, raw_df_valid):
        """Строки без NaT не должны быть удалены."""
        cleaner = DataCleaner(config, raw_df_valid)
        cleaner.step2_drop_null_datetimes()
        assert len(cleaner.df) == len(raw_df_valid)


# ══════════════════════════════════════════════════════════════════════════════
# Шаг 3: переименование колонок
# ══════════════════════════════════════════════════════════════════════════════
class TestStep3RenameColumns:
    def test_russian_columns_appear(self, config, raw_df_valid):
        cleaner = DataCleaner(config, raw_df_valid)
        cleaner.step3_rename_columns()
        assert "мили" in cleaner.df.columns

    def test_original_columns_removed(self, config, raw_df_valid):
        cleaner = DataCleaner(config, raw_df_valid)
        cleaner.step3_rename_columns()
        assert "trip_miles" not in cleaner.df.columns

    def test_all_columns_renamed(self, config, raw_df_valid):
        """Все ключи COLUMNS должны исчезнуть, все значения — появиться."""
        cleaner = DataCleaner(config, raw_df_valid)
        cleaner.step3_rename_columns()
        for old, new in config.COLUMNS.items():
            assert old not in cleaner.df.columns
            assert new in cleaner.df.columns


# ══════════════════════════════════════════════════════════════════════════════
# run_all: интеграционный тест — проверяем производные колонки и типы
# ══════════════════════════════════════════════════════════════════════════════
class TestRunAll:
    DERIVED_COLS = ["километры", "тариф_за_км", "ожидание_мин", "час_суток", "день_недели"]

    @pytest.mark.parametrize("col", DERIVED_COLS)
    def test_derived_columns_exist(self, config, raw_df_valid, col):
        """run_all должен добавить все производные колонки."""
        result = DataCleaner(config, raw_df_valid).run_all()
        assert col in result.columns

    def test_km_calculation(self, config, raw_df_valid):
        """километры = мили * 1.60934, округлённые до 3 знаков."""
        result = DataCleaner(config, raw_df_valid).run_all()
        expected = round(5.0 * 1.60934, 3)
        assert abs(result["километры"].iloc[0] - expected) < 1e-3

    def test_flags_are_bool(self, config, raw_df_valid):
        """Флаги wav_* должны стать булевым типом."""
        result = DataCleaner(config, raw_df_valid).run_all()
        assert result["запрос_для_инвалида"].dtype == bool
        assert result["поездка_для_инвалида"].dtype == bool

    def test_hour_of_day(self, config, raw_df_valid):
        """час_суток должен совпадать с часом из pickup_datetime."""
        result = DataCleaner(config, raw_df_valid).run_all()
        assert result["час_суток"].iloc[0] == 8


# ══════════════════════════════════════════════════════════════════════════════
# Исключения: EmptyDatasetError
# ══════════════════════════════════════════════════════════════════════════════
class TestEmptyDatasetError:
    def test_raised_when_no_files(self, tmp_path):
        """DataLoader.load_raw() должен кинуть EmptyDatasetError при пустой папке."""
        cfg = Config()
        cfg.data_dir = str(tmp_path)   # пустая временная директория
        loader = DataLoader(cfg)
        with pytest.raises(EmptyDatasetError, match="Не найдено файлов"):
            loader.load_raw()

    def test_raised_when_all_rows_are_zeros(self, config):
        """run_all() должен кинуть EmptyDatasetError, если все строки нулевые."""
        all_zeros = pd.DataFrame(
            {
                "request_datetime":     pd.to_datetime(["2021-01-01 08:00:00"]),
                "on_scene_datetime":    pd.to_datetime(["2021-01-01 08:05:00"]),
                "pickup_datetime":      pd.to_datetime(["2021-01-01 08:10:00"]),
                "dropoff_datetime":     pd.to_datetime(["2021-01-01 08:40:00"]),
                "trip_miles":           [0.0],
                "trip_time":            [0.0],
                "base_passenger_fare":  [0.0],
                "tolls":                [0.0],
                "sales_tax":            [0.0],
                "congestion_surcharge": [0.0],
                "tips":                 [0.0],
                "driver_pay":           [0.0],
                "wav_request_flag":     ["N"],
                "wav_match_flag":       ["N"],
            }
        )
        with pytest.raises(EmptyDatasetError):
            DataCleaner(config, all_zeros).run_all()


# ══════════════════════════════════════════════════════════════════════════════
# Strategy: DataExporter
# ══════════════════════════════════════════════════════════════════════════════
class TestDataExporter:
    def test_csv_export_creates_file(self, tmp_path, config, raw_df_valid):
        """CSVExportStrategy создаёт .csv файл."""
        cfg = Config()
        cfg.output_dir = str(tmp_path)
        result = DataCleaner(cfg, raw_df_valid).run_all()
        out = DataExporter(cfg, CSVExportStrategy()).export(result)
        assert out.exists()
        assert out.suffix == ".csv"

    def test_json_export_creates_file(self, tmp_path, raw_df_valid):
        """JSONExportStrategy создаёт .json файл."""
        cfg = Config()
        cfg.output_dir = str(tmp_path)
        result = DataCleaner(cfg, raw_df_valid).run_all()
        out = DataExporter(cfg, JSONExportStrategy()).export(result)
        assert out.exists()
        assert out.suffix == ".json"

    def test_set_strategy_switches_format(self, tmp_path, raw_df_valid):
        """set_strategy() меняет формат без пересоздания DataExporter."""
        cfg = Config()
        cfg.output_dir = str(tmp_path)
        result = DataCleaner(cfg, raw_df_valid).run_all()
        exporter = DataExporter(cfg)                      # по умолчанию CSV
        exporter.set_strategy(JSONExportStrategy())       # переключаем на JSON
        out = exporter.export(result)
        assert out.suffix == ".json"
