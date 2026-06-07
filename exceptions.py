class DataValidationError(Exception):
    """
    Поднимается когда не удалось привести к нужному типу при потоковом чтении
    """

    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(message)
        self.field = field
        self.value = value

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.field is not None:
            parts.append(f"поле: {self.field!r}")
        if self.value is not None:
            parts.append(f"значение: {self.value!r}")
        return " | ".join(parts)


class EmptyDatasetError(Exception):
    """
    Поднимается в двух ситуациях:
      1. DataLoader.load_raw() не нашёл ни одного файла по заданному шаблону
      2. DataCleaner.run_all() вернул пустой DataFrame после всех шагов очистки
    """
