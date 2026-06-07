import pandas as pd
import pathlib
from dataclasses import dataclass, field
from datetime import datetime


# ──────────────────────────────────────────────
def log_step(method):
    """Логирует название шага и кол-во строк до/после"""
    def wrapper(self) -> "DataCleaner":
        before = len(self.df)
        result = method(self)
        after = len(self.df)
        dropped = before - after
        tag = f"[{method.__name__}]"
        print(f"{tag:35} строк: {after:>10,}", end="  ")
        if dropped:
            print(f"(удалено: {dropped:,})", end="")
        print()

        return result
    return wrapper


class Timer:
    """Контекстный менеджер для засечения времени выполнения кода"""
    def __init__(self, name = "Код"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        print(f"{self.name} начался...", end=" ")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        elapsed = self.end_time - self.start_time
        min, sec = map(int, divmod(elapsed.total_seconds(), 60))

        print(f"завершился")
        print(f"Прошло времени: {min:02}:{sec:02}")

        if exc_type is not None:
            print(f"❌ Ошибка: {exc_val}")

        return False  # Пробросить исключение, если оно было


# ──────────────────────────────────────────────
@dataclass
class Config:
    data_dir: str = "DataSet"
    output_dir: str = "DataSet"
    raw_file_pattern: str = "*.parquet"
    cleaned_file_name: str = "поездки_обработанные.csv"
    _encoding: str = field(default="utf-8-sig", repr=False)  # BOM для Excel

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def output_path(self) -> pathlib.Path:
        return pathlib.Path(self.output_dir)

    # Выполняет 2 фукнции:
    # 1) Какие колонны из сырых данных собираем (это ключи)
    # 2) Что на что переименовываем
    COLUMNS = {
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

    ADDED_COLUMNS = {
        "километры":            float,
        "тариф_за_км":          float,
        "ожидание_мин":         float,
        "час_суток":            int,
        "день_недели":          str,
    }

    COLUMNS_TYPE = {
        "время_запроса":        datetime,
        "время_прибытия":       datetime,
        "начало_поездки":       datetime,
        "конец_поездки":        datetime,
        "мили":                 float,
        "время_в_пути_сек":     float,
        "тариф":                float,
        "дорожные_сборы":       float,
        "налог":                float,
        "надбавка_за_пробки":   float,
        "чаевые":               float,
        "выплата_водителю":     float,
        "запрос_для_инвалида":  bool,
        "поездка_для_инвалида": bool,
    }
    COLUMNS_TYPE.update(ADDED_COLUMNS)

    # Какой тип как мы хотим переводить из строки
    CONVERT_FUNCS = {
        int:        int,
        float:      float,
        str:        str,
        bool:       lambda string: string=="True",
        datetime:   lambda string: datetime.strptime(string, "%Y-%m-%d %H:%M:%S"),
    }


# ──────────────────────────────────────────────
class DataLoader:
    def __init__(self, config: Config):
        self.config = config

    def load_raw(self) -> pd.DataFrame:
        frames = []
        for path in pathlib.Path(self.config.data_dir).glob(self.config.raw_file_pattern):
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
        clean_df = DataCleaner(raw_df).run_all()
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
        self.df = self.df.rename(columns=self.config.COLUMN_RENAME)
        return self

    @log_step
    def step4_cast_datetimes(self) -> "DataCleaner":
        """Приводим временные колонки к datetime64"""
        datetime_cols = [name for name, type in self.config.COLUMNS_TYPE if type is datetime]

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
    def __init__(self, config: Config):
        self.config = config

    def to_csv(self, df: pd.DataFrame, filename: str = "поездки_обработанные.csv") -> pathlib.Path:
        with Timer("Экспорт в csv"):
            self.config.output_path.mkdir(exist_ok=True)
            out = self.config.output_path / filename
            df.to_csv(out, index=False, encoding=self.config.encoding)

        print(f"Сохранено: {len(df):,} строк → {out}")
        return out

