import pandas as pd
import pathlib
from dataclasses import dataclass, field


# ──────────────────────────────────────────────
def log_step(method):
    """Логирует название шага и кол-во строк до/после"""
    def wrapper(self) -> "DataCleaner":
        before = len(self.df)
        result = method(self)
        after = len(self.df)
        dropped = before - after
        tag = f"[{method.__name__}]"
        if dropped:
            print(f"{tag:35} строк: {after:>10,}  (удалено: {dropped:,})")
        else:
            print(f"{tag:35} строк: {after:>10,}")
        return result
    return wrapper


# ──────────────────────────────────────────────
@dataclass
class PipelineConfig:
    data_dir: str = "DataSet"
    output_dir: str = "DataSet"
    file_pattern: str = "*.parquet"
    _encoding: str = field(default="utf-8-sig", repr=False)  # BOM для Excel

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def output_path(self) -> pathlib.Path:
        return pathlib.Path(self.output_dir)


# ──────────────────────────────────────────────
class DataLoader:
    VALUABLE_COLUMNS = [
        "request_datetime",
        "on_scene_datetime",
        "pickup_datetime",
        "dropoff_datetime",
        "trip_miles",
        "trip_time",
        "base_passenger_fare",
        "tolls",
        "sales_tax",
        "congestion_surcharge",
        "tips",
        "driver_pay",
        "wav_request_flag",
        "wav_match_flag",
    ]

    def __init__(self, config: PipelineConfig):
        self.config = config

    def load(self) -> pd.DataFrame:
        frames = []
        for path in pathlib.Path(self.config.data_dir).glob(self.config.file_pattern):
            temp = pd.read_parquet(path, columns=self.VALUABLE_COLUMNS)
            frames.append(temp)
            print(f"  Загружен: {path.name}  ({len(temp):,} строк)")
        df = pd.concat(frames, ignore_index=True)
        print(f"Итого загружено: {len(df):,} строк\n")
        return df


# ──────────────────────────────────────────────
class DataCleaner:
    COLUMN_RENAME = {
        "request_datetime":     "время_запроса",
        "on_scene_datetime":    "время_прибытия",
        "pickup_datetime":      "начало_поездки",
        "dropoff_datetime":     "конец_поездки",
        "trip_miles":           "мили",
        "trip_time":            "время_в_пути_сек",
        "base_passenger_fare":  "тариф",
        "tolls":                "дорожные_сборы",
        "sales_tax":            "налог",
        "congestion_surcharge": "надбавка_за_пробки",
        "tips":                 "чаевые",
        "driver_pay":           "выплата_водителю",
        "wav_request_flag":     "запрос_для_инвалида",
        "wav_match_flag":       "поездка_для_инвалида",
    }

    DATETIME_COLUMNS = [
        "время_запроса", "время_прибытия",
        "начало_поездки", "конец_поездки",
    ]

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    @log_step
    def step1_drop_zero_trips(self) -> "DataCleaner":
        """Удаляем строки где trip_miles / trip_time / driver_pay == 0"""
        mask = (
            (self.df["driver_pay"] != 0) &
            (self.df["trip_time"]  != 0) &
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
        self.df = self.df.rename(columns=self.COLUMN_RENAME)
        return self

    @log_step
    def step4_cast_datetimes(self) -> "DataCleaner":
        """Приводим временные колонки к datetime64"""
        for col in self.DATETIME_COLUMNS:
            self.df[col] = pd.to_datetime(self.df[col], errors="coerce")
        # Заодно чистим NaT которые могли появиться после конвертации
        self.df = self.df.dropna(subset=self.DATETIME_COLUMNS).copy()
        return self

    @log_step
    def step5_add_derived_columns(self) -> "DataCleaner":
        """Добавляем колонки: ожидание, км, тариф/км, час суток"""
        df = self.df

        df["ожидание_мин"] = (
            (df["начало_поездки"] - df["время_запроса"])
            .dt.total_seconds()
            .div(60)
            .round(2)
        )
        df["километры"] = (df["мили"] * 1.60934).round(2)
        df["тариф_за_км"] = (
            df["тариф"] / df["километры"].replace(0, float("nan"))
        ).round(2)
        df["час_суток"] = df["начало_поездки"].dt.hour
        df["день_недели"] = df["начало_поездки"].dt.day_name()

        self.df = df
        return self

    @log_step
    def step6_convert_flags(self) -> "DataCleaner":
        """Конвертируем Y/N флаги в bool"""
        cols = ["запрос_для_инвалида", "поездка_для_инвалида"]
        self.df[cols] = (self.df[cols] == "Y")
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
    def __init__(self, config: PipelineConfig):
        self.config = config

    def to_csv(self, df: pd.DataFrame, filename: str = "поездки_обработанные.csv") -> pathlib.Path:
        self.config.output_path.mkdir(exist_ok=True)
        out = self.config.output_path / filename
        df.to_csv(out, index=False, encoding=self.config.encoding)
        print(f"\nСохранено: {len(df):,} строк → {out}")
        return out

