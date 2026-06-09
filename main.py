from data_processing import DataLoader, DataCleaner, DataExporter
from config_and_tools import Timer, Config
from iterators import TripIterable, MapIterator, FilterIterator
from strategies import CSVExportStrategy, JSONExportStrategy


if __name__ == "__main__":
    config = Config()
    config.raw_file_pattern = "*01.parquet"  # только 1 файл, чтобы не так много ждать
    loader = DataLoader(config)

    # Отдельно экспортируем в json
    # config.DEFAULT_EXPORT_STRATEGY = JSONExportStrategy()
    # config.cleaned_file_name = "данные_в_json"

    # with Timer("Экспорт из сырых данных"):
    #     df = DataCleaner(config, loader.load_raw()).run_all()
    #     DataExporter(config).export(df)

    # # Если чистых данных нет, то оно само запустит pipeline
    # clean_df = loader.get_data()
    # del clean_df  # использовать будем ленивые итераторы

    print("начинаем лениво")

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
