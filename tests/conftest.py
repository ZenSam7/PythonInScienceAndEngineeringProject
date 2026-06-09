import sys
import pathlib

import pandas as pd
import pytest

# Добавляем корень проекта в sys.path, чтобы тесты находили модули
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from data_processing import Config


# ── Регистрация кастомных marks ───────────────────────────────────────────────
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "processing: тесты модуля data_processing (DataCleaner, DataLoader, DataExporter)",
    )
    config.addinivalue_line(
        "markers",
        "streaming: тесты потоковых итераторов (TripIterator, FilterIterator, MapIterator)",
    )


# ── Фикстуры ──────────────────────────────────────────────────────────────────
@pytest.fixture
def config():
    """Конфиг с настройками по умолчанию"""
    return Config()


@pytest.fixture
def raw_df():
    """
    DataFrame с сырыми данными
    Содержит 2 валидных строки и 1 нулевую
    """
    return pd.DataFrame(
        {
            "request_datetime":     pd.to_datetime(["2021-01-01 08:00:00", "2021-01-01 09:00:00", "2021-01-01 10:00:00"]),
            "on_scene_datetime":    pd.to_datetime(["2021-01-01 08:05:00", "2021-01-01 09:05:00", "2021-01-01 10:05:00"]),
            "pickup_datetime":      pd.to_datetime(["2021-01-01 08:10:00", "2021-01-01 09:10:00", "2021-01-01 10:10:00"]),
            "dropoff_datetime":     pd.to_datetime(["2021-01-01 08:40:00", "2021-01-01 09:40:00", "2021-01-01 10:40:00"]),
            "trip_miles":           [5.0,  3.0,  0.0],
            "trip_time":            [1800.0, 1200.0, 0.0],
            "base_passenger_fare":  [20.0, 15.0, 0.0],
            "tolls":                [0.0,  1.0,  0.0],
            "sales_tax":            [1.5,  1.0,  0.0],
            "congestion_surcharge": [2.5,  2.5,  0.0],
            "tips":                 [3.0,  2.0,  0.0],
            "driver_pay":           [15.0, 11.0, 0.0],
            "wav_request_flag":     ["N",  "N",  "Y"],
            "wav_match_flag":       ["N",  "Y",  "Y"],
        }
    )


@pytest.fixture
def raw_df_valid():
    """
    DataFrame только с валидными строками (без нулей и NaT)
    """
    return pd.DataFrame(
        {
            "request_datetime":     pd.to_datetime(["2021-01-01 08:00:00", "2021-01-01 09:00:00"]),
            "on_scene_datetime":    pd.to_datetime(["2021-01-01 08:05:00", "2021-01-01 09:05:00"]),
            "pickup_datetime":      pd.to_datetime(["2021-01-01 08:10:00", "2021-01-01 09:10:00"]),
            "dropoff_datetime":     pd.to_datetime(["2021-01-01 08:40:00", "2021-01-01 09:40:00"]),
            "trip_miles":           [5.0,  3.0],
            "trip_time":            [1800.0, 1200.0],
            "base_passenger_fare":  [20.0, 15.0],
            "tolls":                [0.0,  1.0],
            "sales_tax":            [1.5,  1.0],
            "congestion_surcharge": [2.5,  2.5],
            "tips":                 [3.0,  2.0],
            "driver_pay":           [15.0, 11.0],
            "wav_request_flag":     ["N",  "Y"],
            "wav_match_flag":       ["N",  "Y"],
        }
    )
