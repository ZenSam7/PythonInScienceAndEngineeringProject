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

