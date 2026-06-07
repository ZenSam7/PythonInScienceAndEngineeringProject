from data_processing import PipelineConfig, DataLoader, DataCleaner, DataExporter
from iterators import TripIterable, MapIterator, FilterIterator


if __name__ == "__main__":
    config = PipelineConfig()
    loader = DataLoader(config)

    # Если чистых данных нет, то оно само запустит pipeline
    clean_df = loader.get_data()

    # Матрёшка без pandas
    trips = TripIterable(clean_df)

    утренние_выплаты = MapIterator(
        FilterIterator(trips, lambda r: r["час_суток"] == 8),
        lambda r: round(r["выплата_водителю"], 2)
    )

    # Первые 5 значений — лениво, без материализации всего датасета
    for i, pay in enumerate(утренние_выплаты):
        print(pay)
        if i >= 4:
            break
