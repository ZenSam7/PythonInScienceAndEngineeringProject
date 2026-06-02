import pandas as pd
import pathlib

datasets_folder = pathlib.Path("DataSet")


def load_datas() -> pd.DataFrame:
    """Загружаем файлы"""

    df = pd.DataFrame()
    for i in datasets_folder.glob("*.parquet"):
        # Объединяем все файлы
        temp = pd.read_parquet(r"DataSet\fhvhv_tripdata_2021-01.parquet")

        # Оставляем только понятные колонны
        valuable_datas = temp.loc[:,
                         [
                             "request_datetime",  # Время запроса
                             "on_scene_datetime",  # Время прибытия
                             "pickup_datetime",  # Когда в такси зашли
                             "dropoff_datetime",  # Когда из него вышли
                             "trip_miles",  # Пройденные мили
                             "trip_time",  # Пройденное время

                             "base_passenger_fare",  # Тариф
                             "tolls",  # Общая сумма
                             "sales_tax",  # Налог Нью-Йорку
                             "congestion_surcharge",  # Общая собранная сумма всего (?)
                             "tips",  # Чаевые
                             "driver_pay",  # Прибыль водителя (после вычета)

                             "wav_request_flag",  # Такси вызывали для инвалида? Y/N
                             "wav_match_flag"  # Совершалась ли поезда для инвалида?
                         ]
                         ]

        df = pd.concat([df, valuable_datas], ignore_index=True)

    return df


def clean_datas(df: pd.DataFrame) -> pd.DataFrame:
    """Чистим строки где поездка не имеет смысла"""
    before = len(df)
    df = df[(df["driver_pay"] != 0) & (df["trip_time"] != 0) & (df["trip_miles"] != 0)]
    after = len(df)
    print(f"Удалено строк: {before - after} ({(before - after) / before * 100:.2f}%)")

    return df


def normalize_datas(df: pd.DataFrame) -> pd.DataFrame:
    """Нормализуем на русский лад"""
    # --- Переименование колонок ---
    COLUMN_RENAME = {
        "request_datetime": "время_запроса",
        "on_scene_datetime": "время_прибытия",
        "pickup_datetime": "начало_поездки",
        "dropoff_datetime": "конец_поездки",
        "trip_miles": "мили",
        "trip_time": "время_в_пути_сек",
        "base_passenger_fare": "тариф",
        "tolls": "дорожные_сборы",
        "sales_tax": "налог",
        "congestion_surcharge": "надбавка_за_пробки",
        "tips": "чаевые",
        "driver_pay": "выплата_водителю",
        "wav_request_flag": "запрос_для_инвалида",
        "wav_match_flag": "поездка_для_инвалида",
    }
    df = df.rename(columns=COLUMN_RENAME)

    # --- Типы дат ---
    for col in ["время_запроса", "время_прибытия", "начало_поездки", "конец_поездки"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # --- Производные колонки (имеют аналитический смысл) ---
    # Время ожидания от запроса до посадки (в минутах)
    df["ожидание_мин"] = (
        (df["начало_поездки"] - df["время_запроса"])
        .dt.total_seconds()
        .div(60)
        .round(2)
    )

    # Перевод миль в километры
    df["километры"] = (df["мили"] * 1.60934).round(2)

    # Стоимость за километр
    df["тариф_за_км"] = (df["тариф"] / df["километры"].replace(0, float("nan"))).round(2)

    # Час суток — для пиковых анализов
    df["час_суток"] = df["начало_поездки"].dt.hour

    # Флаги Y/N → bool (удобнее фильтровать)
    for col in ["запрос_для_инвалида", "поездка_для_инвалида"]:
        df[col] = df[col].map({"Y": True, "N": False})

    return df

def save_datas(df: pd.DataFrame):
    """Сохраняем"""
    # CSV — с явной кодировкой чтобы кириллица не сломалась
    df.to_csv(datasets_folder / "поездки_обработанные.csv", index=False, encoding="utf-8-sig")
    print(f"Сохранено: {len(df):,} строк → {datasets_folder / 'поездки_обработанные.csv'}")


if __name__ == "__main__":
    print(pd.read_csv(datasets_folder/"поездки_обработанные.csv").head(30))

    # df = load_datas()
    # df = clean_datas(df)
    # df = normalize_datas(df)
    # save_datas(df)

    # Матрёшка породнее будет))
    # save_datas(
    #     normalize_datas(
    #         clean_datas(
    #             load_datas()
    #         )
    #     )
    # )
