# Анализ поездок Uber NYC (2021)

Датасет взят из
[Kaggle](https://www.kaggle.com/datasets/shuhengmo/uber-nyc-forhire-vehicles-trip-data-2021?select=data_dictionary_trip_records_hvfhs.pdf)
за 2021 год.

## Поля данных (которые используются)

| Поле (сырое)          | Поле (обработанное)    | Смысл                              |
|-----------------------|------------------------|------------------------------------|
| `request_datetime`    | `время_запроса`        | Когда пассажир вызвал такси        |
| `on_scene_datetime`   | `время_прибытия`       | Когда машина прибыла               |
| `pickup_datetime`     | `начало_поездки`       | Когда пассажир сел                 |
| `dropoff_datetime`    | `конец_поездки`        | Когда пассажир вышел               |
| `trip_miles`          | `мили`                 | Пройденное расстояние (мили)       |
| `trip_time`           | `время_в_пути_сек`     | Длительность поездки (сек)         |
| `base_passenger_fare` | `тариф`                | Базовый тариф ($)                  |
| `tolls`               | `дорожные_сборы`       | Дорожные сборы ($)                 |
| `sales_tax`           | `налог`                | Налог ($)                          |
| `congestion_surcharge`| `надбавка_за_пробки`   | Надбавка за пробки ($)             |
| `tips`                | `чаевые`               | Чаевые ($)                         |
| `driver_pay`          | `выплата_водителю`     | Выплата водителю ($)               |
| `wav_request_flag`    | `запрос_для_инвалида`  | Вызывали WAV? (bool)               |
| `wav_match_flag`      | `поездка_для_инвалида` | Поездка на WAV? (bool)             |

Добавленные колонки: `километры`, `тариф_за_км`, `ожидание_мин`, `час_суток`, `день_недели`.

---

## Структура проекта

```
├── data_processing.py   # Config, DataLoader, DataCleaner, DataExporter
├── config_and_tools.py  # Confit, Timer, log_step
├── iterators.py         # TripIterable, TripIterator, FilterIterator, MapIterator
├── strategies.py        # ExportStrategy (ABC), CSVExportStrategy, JSONExportStrategy
├── errors.py            # DataValidationError, EmptyDatasetError
├── main.py              # Точка входа
├── DataSet/             # Сюда кладём .parquet файлы и сюда же пишется CSV
└── tests/
    ├── conftest.py              # Фикстуры + регистрация marks
    ├── test_data_processing.py  # Тесты DataCleaner, DataLoader, DataExporter (23 теста)
    └── test_iterators.py        # Тесты итераторов (13 тестов)
```

---

## Как запустить обработку

1. Скачать датасет и положить `.parquet`-файлы в папку `DataSet/`.
2. Запустить:
   ```bash
   pip install -r req.txt
   python main.py
   ```
3. Файл `DataSet/обработанные_поездки.csv` создаётся автоматически.

При повторном запуске пайплайн пропускается — сразу читает готовый CSV.

---

## Как запустить тесты

```bash
python -m pytest tests/ -v
```

Запуск только одной группы:
```bash
python -m pytest tests/ -m processing    # тесты DataCleaner / DataLoader
python -m pytest tests/ -m streaming     # тесты итераторов
```

---

## Что создаётся на выходе

| Файл                                    | Содержимое                              |
|-----------------------------------------|-----------------------------------------|
| `DataSet/обработанные_поездки.csv`      | Очищенный датасет (CSV, UTF-8 BOM)      |
| `DataSet/обработанные_поездки.json`     | То же в JSON (если передать JSONExportStrategy) |

---

## Архитектурные решения

### Паттерн: Strategy (в `strategies.py`)
`DataExporter` — интерфейс для экспорта (абстрактный класс)
Имплеменцирует её переданная стратегия (`CSVExportStrategy()` / `JSONExportStrategy()`) 

```python
# CSV (по умолчанию)
DataExporter(config).export(df)

# Переключение на JSON без пересоздания объекта
exporter = DataExporter(config)
exporter.set_strategy(JSONExportStrategy())
exporter.export(df)
```
> пожалуйста, всегда инициализируйте стратегию перед тем как её передать

### Декоратор: `@log_step`
Оборачивает каждый шаг `DataCleaner`: печатает имя шага, кол-во строк
до/после и число удалённых строк. Применён ко всем 6 методам `step*`
### Контекстный менеджер: `Timer`
Позволяет засечь время выполнения участка кода. Передавать можно любой объект (он будет использован в качестве имени) 

### Пользовательские исключения (`exceptions.py`)
| Исключение            | Где поднимается                                         | Где ловится              |
|-----------------------|---------------------------------------------------------|--------------------------|
| `EmptyDatasetError`   | `DataLoader.load_raw()` (нет файлов)                    | Вызывающий код / тесты   |
|                       | `DataCleaner.run_all()` (DataFrame пуст после очистки)  | Вызывающий код / тесты   |
| `DataValidationError` | `TripIterator._cast()` (поле не конвертируется)          | Вызывающий код / тесты   |

### Тестирование
- **36 тест-кейсов** (18 параметризованных)
- `@pytest.fixture` — `config`, `raw_df`, `raw_df_valid`, `iterator_with_header`
- `@pytest.mark.parametrize` — пороги фильтрации, нулевые колонки, производные колонки
- `pytest.raises` — `EmptyDatasetError`, `DataValidationError`, `FileNotFoundError`
- `@pytest.mark.processing` / `@pytest.mark.streaming` — кастомные метки
