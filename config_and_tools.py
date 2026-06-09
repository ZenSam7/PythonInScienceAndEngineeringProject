from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from strategies import CSVExportStrategy, ExportStrategy, JSONExportStrategy


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


# ──────────────────────────────────────────────
class Timer:
    """Контекстный менеджер для засечения времени выполнения кода"""

    def __init__(self, name="Код"):
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
    cleaned_file_name: str = "обработанные_поездки"  # Без расширения
    _encoding: str = field(default="utf-8-sig", repr=False)  # BOM для Excel

    DEFAULT_EXPORT_STRATEGY: ExportStrategy = CSVExportStrategy()

    def get_full_cleaned_file_name(self, strategy: ExportStrategy or None = None) -> str:
        return self.config.cleaned_file_name + strategy.file_extension() if strategy \
            else self.cleaned_file_name + self.DEFAULT_EXPORT_STRATEGY.file_extension

    def get_full_file_path(self, strategy: ExportStrategy or None = None) -> Path:
        return self.output_path / self.get_full_cleaned_file_name(strategy)

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir)

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
        int:      int,
        float:    float,
        str:      str,
        bool: lambda string: string == "True",
        datetime: lambda string: datetime.strptime(string, "%Y-%m-%d %H:%M:%S"),
    }
