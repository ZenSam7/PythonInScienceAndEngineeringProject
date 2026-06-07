from __future__ import annotations  # Убираем ошибки с аннотацией типов
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, field
from config_and_tools import Timer, log_step, Config, datetime
from strategies import ExportStrategy


# ──────────────────────────────────────────────
class DataLoader:
    def __init__(self, config: Config):
        self.config = config

    def load_raw(self) -> pd.DataFrame:
        Path(self.config.data_dir).mkdir(exist_ok=True)
        frames = []

        for path in Path(self.config.data_dir).glob(self.config.raw_file_pattern):
            temp = pd.read_parquet(path, columns=list(self.config.COLUMNS.keys()))
            frames.append(temp)
            print(f"  Загружен: {path.name}  ({len(temp):,} строк)")

        # Исключение
        if not frames:
            raise EmptyDatasetError(
                f"Не найдено файлов по шаблону '{self.config.raw_file_pattern}' "
                f"в директории '{self.config.data_dir}'\n"
                f"Скачайте датасет по ссылке в README"
            )

        df = pd.concat(frames, ignore_index=True)
        print(f"Итого загружено: {len(df):,} строк\n")
        return df

    def load_clean(self) -> pd.DataFrame:
        """Загружает уже обработанный CSV"""
        path = Path(self.config.output_dir) / self.config.cleaned_file_name
        if not path.exists():
            raise FileNotFoundError(f"Чистых данных нет: {path}")
        df = pd.read_csv(path, encoding=self.config.encoding)
        print(f"Загружен чистый датасет: {len(df):,} строк ← {path}")
        return df

    def get_data(self, strategy: ExportStrategy or None = None) -> pd.DataFrame:
        """Если есть уже очищенные данные — открываем их
        Если нет — обрабатываем сырые данные"""
        clean_path = self.config.output_path / self.config.cleaned_file_name

        if clean_path.exists():
            print("Найден чистый датасет, пропускаем обработку")
            return self.load_clean()

        print("Чистых данных нет — запускаем пайплайн")
        raw_df = self.load_raw()
        clean_df = DataCleaner(self.config, raw_df).run_all()
        DataExporter(self.config, strategy).export(clean_df)
        return clean_df


# ──────────────────────────────────────────────
class DataCleaner:
    def __init__(self, config: Config, df: pd.DataFrame):
        self.config = config
        self.df = df.copy()

    @log_step
    def step1_drop_zero_trips(self) -> DataCleaner:
        """Удаляем строки где trip_miles / trip_time / driver_pay == 0"""
        mask = (
                (self.df["driver_pay"] != 0) &
                (self.df["trip_time"] != 0) &
                (self.df["trip_miles"] != 0)
        )
        self.df = self.df[mask].copy()
        return self

    @log_step
    def step2_drop_null_datetimes(self) -> DataCleaner:
        """Удаляем строки с NaT в ключевых временных колонках"""
        self.df = self.df.dropna(
            subset=["pickup_datetime", "dropoff_datetime", "request_datetime"]
        ).copy()
        return self

    @log_step
    def step3_rename_columns(self) -> DataCleaner:
        """Переименовываем колонки на русский лад"""
        self.df = self.df.rename(columns=self.config.COLUMNS)
        return self

    @log_step
    def step4_cast_datetimes(self) -> DataCleaner:
        """Приводим временные колонки к datetime64"""
        datetime_cols = [
            name
            for name, col_type in self.config.COLUMNS_TYPE.items()
            if col_type == datetime
        ]

        for col in datetime_cols:
            self.df[col] = pd.to_datetime(self.df[col], errors="coerce")

        # Чистим NaT которые могли появиться после конвертации
        self.df = self.df.dropna(subset=datetime_cols).copy()
        return self

    @log_step
    def step5_add_derived_columns(self) -> DataCleaner:
        """Добавляем колонки ADDED_COLUMNS: ожидание, км, тариф/км, час суток"""
        df = self.df

        df["ожидание_мин"] = (
            (df["начало_поездки"] - df["время_запроса"])
            .dt.total_seconds()
            .div(60)
            .round(2)
        )
        df["километры"] = (df["мили"] * 1.60934).round(3)
        df["тариф_за_км"] = (
                df["тариф"] / df["километры"].replace(0, float("nan"))
        ).round(3)
        df["час_суток"] = df["начало_поездки"].dt.hour
        df["день_недели"] = df["начало_поездки"].dt.day_name()

        self.df = df
        return self

    @log_step
    def step6_convert_flags(self) -> DataCleaner:
        """Конвертируем Y/N флаги в bool"""
        cols = ["запрос_для_инвалида", "поездка_для_инвалида"]
        self.df[cols] = self.df[cols] == "Y"
        return self

    def run_all(self) -> pd.DataFrame:
        """Запускает все 6 шагов по цепочке"""
        print("=" * 55)
        print("  ПАЙПЛАЙН ОЧИСТКИ ДАННЫХ")
        print("=" * 55)
        result = (
            self
            .step1_drop_zero_trips()
            .step2_drop_null_datetimes()
            .step3_rename_columns()
            .step4_cast_datetimes()
            .step5_add_derived_columns()
            .step6_convert_flags()
            .df
        )

        # Исключение
        if result.empty:
            raise EmptyDatasetError(
                "После очистки данных датафрейм оказался пустым"
            )

        return result


# ──────────────────────────────────────────────
class DataExporter:
    """
    Экспортирует DataFrame, делегируя сохранение стратегии (паттерн Strategy)
    """

    def __init__(self, config: Config, strategy: ExportStrategy | None = None):
        self.config = config
        self._strategy: ExportStrategy = (strategy or config.DEFAULT_EXPORT_STRATEGY)

    def set_strategy(self, strategy: ExportStrategy) -> DataExporter:
        """Меняет стратегию экспорта без пересоздания объекта"""
        if not isinstance(strategy, ExportStrategy):
            raise ValueError(f"{strategy!r} эт не стратегия")

        self._strategy = strategy
        return self

    def export(self, df: pd.DataFrame, filename: str or None = None) -> Path:
        self.config.output_path.mkdir(exist_ok=True)
        fname = (filename or self.config.cleaned_file) + \
            self._strategy.file_extension
        out = self.config.output_path / fname

        with Timer("Экспорт"):
            self._strategy.export(df, out, self.config.encoding)

        print(f"Сохранено: {len(df):,} строк → {out}")
        return out
