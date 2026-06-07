import pandas as pd

from data_processing import Config, DataLoader, DataCleaner, DataExporter, Timer
from iterators import TripIterable, MapIterator, FilterIterator


if __name__ == "__main__":
    config = Config()
    config.raw_file_pattern = "*01.parquet"  # только 1 файл, чтобы не так много ждать
    loader = DataLoader(config)

    # # Если чистых данных нет, то оно само запустит pipeline
    # clean_df = loader.get_data()

    # Матрёшка без pandas
    trips = TripIterable(config)

    утренние_выплаты = MapIterator(
        FilterIterator(trips, lambda r: 6 <= r["час_суток"] <= 10),
        lambda r: r["выплата_водителю"]
    )

    # Первые 10 значений — лениво, без материализации всего датасета
    for i, выплата in enumerate(утренние_выплаты):
        print(выплата)
        if i >= 9:
            break