VALID_TYPES = {"int", "str", "bool"}


def create_table(metadata, table_name, columns):
    """Создаёт таблицу со столбцом ID:int в начале. Возвращает метаданные."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    table_columns = {"ID": "int"}
    for column in columns:
        name, separator, column_type = column.partition(":")
        if not separator or not name or column_type not in VALID_TYPES:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata
        if name == "ID" and column_type == "int":
            continue  # ID задан пользователем явно — он уже есть
        if name in table_columns:
            print(f"Некорректное значение: {column}. Столбец уже указан.")
            return metadata
        table_columns[name] = column_type

    metadata[table_name] = {"columns": table_columns}
    columns_text = ", ".join(f"{name}:{kind}" for name, kind in table_columns.items())
    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_text}')
    return metadata


def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных. Возвращает метаданные."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Выводит список всех таблиц."""
    if not metadata:
        print("Таблиц пока нет.")
        return
    for table_name in metadata:
        print(f"- {table_name}")
