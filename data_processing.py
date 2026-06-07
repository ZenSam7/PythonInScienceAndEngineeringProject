import pandas as pd
import pathlib
from dataclasses import dataclass, field
from config_and_tools import Timer, log_step, Config,datetime


# ──────────────────────────────────────────────
class DataLoader:
    def __init__(self, config: Config):
        self.config = config

    def load_raw(self) -> pd.DataFrame:
        frames = []
        for path in pathlib.Path(self.config.data_dir). \
                glob(self.config.raw_file_pattern):
            temp = pd.read_parquet(path, columns=list(self.config.COLUMNS.keys()))
            frames.append(temp)
            print(f"  Загружен: {path.name}  ({len(temp):,} строк)")
        df = pd.concat(frames, ignore_index=True)
        print(f"Итого загружено: {len(df):,} строк\n")
        return df

    def load_clean(self) -> pd.DataFrame:
        """Загружает уже обработанный CSV"""
        path = pathlib.Path(self.config.output_dir) / self.config.cleaned_file_name
        if not path.exists():
            raise FileNotFoundError(f"Чистых данных нет: {path}")
        df = pd.read_csv(path, encoding=self.config.encoding)
        print(f"Загружен чистый датасет: {len(df):,} строк ← {path}")
        return df

    def get_data(self) -> pd.DataFrame:
        """Если есть уже очищенные данные, то открываем сначала их.
        если нету, то обрабатываем сырые данные"""
        clean_path = self.config.output_path / self.config.cleaned_file_name

        if clean_path.exists():
            print("Найден чистый датасет, пропускаем обработку")
            return self.load_clean()

        print("Чистых данных нет — запускаем пайплайн")
        raw_df = self.load_raw()
        clean_df = DataCleaner(self.config, raw_df).run_all()
        DataExporter(self.config).to_csv(clean_df)
        return clean_df


# ──────────────────────────────────────────────
class DataCleaner:
    def __init__(self, config: Config, df: pd.DataFrame):
        self.config = config
        self.df = df.copy()

    @log_step
    def step1_drop_zero_trips(self) -> "DataCleaner":
        """Удаляем строки где trip_miles / trip_time / driver_pay == 0"""
        mask = (
                (self.df["driver_pay"] != 0) &
                (self.df["trip_time"] != 0) &
                (self.df["trip_miles"] != 0)
        )
        self.df = self.df[mask].copy()
        return self

    @log_step
    def step2_drop_null_datetimes(self) -> "DataCleaner":
        """Удаляем строки с NaT в ключевых временных колонках"""
        self.df = self.df.dropna(
            subset=["pickup_datetime", "dropoff_datetime", "request_datetime"]
        ).copy()
        return self

    @log_step
    def step3_rename_columns(self) -> "DataCleaner":
        """Переименовываем колонки на русский лад"""
        self.df = self.df.rename(columns=self.config.COLUMNS)
        return self

    @log_step
    def step4_cast_datetimes(self) -> "DataCleaner":
        """Приводим временные колонки к datetime64"""
        datetime_cols = [
            name
            for name, type in self.config.COLUMNS_TYPE.items()
            if type == datetime
        ]

        for col in datetime_cols:
            self.df[col] = pd.to_datetime(self.df[col], errors="coerce")
        # Заодно чистим NaT которые могли появиться после конвертации
        self.df = self.df.dropna(subset=datetime_cols).copy()
        return self

    @log_step
    def step5_add_derived_columns(self) -> "DataCleaner":
        """Добавляем колонки: ожидание, км, тариф/км, час суток
        ADDED_COLUMNS"""
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
    def step6_convert_flags(self) -> "DataCleaner":
        """Конвертируем Y/N флаги в bool"""
        cols = ["запрос_для_инвалида", "поездка_для_инвалида"]
        self.df[cols] = self.df[cols] == "Y"
        return self

    def run_all(self) -> pd.DataFrame:
        """Запускает все 6 шагов по цепочке"""
        print("=" * 55)
        print("  ПАЙПЛАЙН ОЧИСТКИ ДАННЫХ")
        print("=" * 55)
        return (
            self
            .step1_drop_zero_trips()
            .step2_drop_null_datetimes()
            .step3_rename_columns()
            .step4_cast_datetimes()
            .step5_add_derived_columns()
            .step6_convert_flags()
            .df
        )


# ──────────────────────────────────────────────
class DataExporter:
    def __init__(self, config: Config):
        self.config = config

    def to_csv(self, df: pd.DataFrame, filename: str = "поездки_обработанные.csv") -> pathlib.Path:
        with Timer("Экспорт в csv"):
            self.config.output_path.mkdir(exist_ok=True)
            out = self.config.output_path / filename
            df.to_csv(out, index=False, encoding=self.config.encoding)

        print(f"Сохранено: {len(df):,} строк → {out}")
        return out
