from data_processing import PipelineConfig, DataLoader, DataCleaner, DataExporter
from iterators import TripIterable, MapIterator, FilterIterator


if __name__ == "__main__":
    config = PipelineConfig()

    raw_df   = DataLoader(config).load()
    clean_df = DataCleaner(raw_df).run_all()
    DataExporter(config).to_csv(clean_df)

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
