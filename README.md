Датасет взят из 
[Kaggle](https://www.kaggle.com/datasets/shuhengmo/uber-nyc-forhire-vehicles-trip-data-2021?select=data_dictionary_trip_records_hvfhs.pdf) 
за январь 2021 года.


Поля данных (которые используются):

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


# Как запустить:
1) скачать датасет и закинуть в папку DataSet (файлы типа `fhvhv_tripdata_2021-01.parquet`, можно хоть все скачать)
2) `python main.py` (по умолчанию после обработки сырых данных создаст в этой же папке "поездки_обработанные.csv")
