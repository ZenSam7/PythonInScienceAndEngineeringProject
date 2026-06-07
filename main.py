from data_processing import DataLoader, DataCleaner, DataExporter
from config_and_tools import Timer, Config
from iterators import TripIterable, MapIterator, FilterIterator
from strategies import CSVExportStrategy


if __name__ == "__main__":
    config = Config()
    config.raw_file_pattern = "*01.parquet"  # только 1 файл, чтобы не так много ждать
    config.DEFAULT_EXPORT_STRATEGY = CSVExportStrategy()
    loader = DataLoader(config)

    # # Если чистых данных нет, то оно само запустит pipeline
    # clean_df = loader.get_data()
    # del clean_df  # использовать будем ленивые итераторы

    trips = TripIterable(config)

    # Матрёшка без pandas
    утренние_выплаты = MapIterator(
        FilterIterator(trips, lambda r: 6 <= r["час_суток"] <= 10),
        lambda r: r["выплата_водителю"],
    )

    # Первые 10 значений, без материализации всего датасета
    for i, выплата in enumerate(утренние_выплаты):
        print(выплата)
        if i >= 9:
            break
