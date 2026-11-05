from primitive_db.utils import load_table_data

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


TYPES = {"int": int, "str": str, "bool": bool}


def check_type(value, type_name):
    """Проверяет тип значения. bool и int различаются строго."""
    return type(value) is TYPES[type_name]


def validate_clause(metadata, table_name, clause):
    """Проверяет, что столбцы условия существуют, а значения нужного типа."""
    columns = metadata[table_name]["columns"]
    for column, value in clause.items():
        if column not in columns:
            print(f'Ошибка: Столбца "{column}" нет в таблице "{table_name}".')
            return False
        if not check_type(value, columns[column]):
            print(f"Некорректное значение: {value}. Попробуйте снова.")
            return False
    return True


def insert(metadata, table_name, values):
    """Добавляет запись с автоматическим ID. Возвращает данные таблицы или None."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None

    schema = [
        (name, kind)
        for name, kind in metadata[table_name]["columns"].items()
        if name != "ID"
    ]
    if len(values) != len(schema):
        print(
            f"Некорректное значение: ожидается {len(schema)} значений, "
            f"получено {len(values)}. Попробуйте снова."
        )
        return None
    for (name, kind), value in zip(schema, values):
        if not check_type(value, kind):
            print(f"Некорректное значение: {value}. Столбец {name} имеет тип {kind}.")
            return None

    table_data = load_table_data(table_name)
    new_id = max((record["ID"] for record in table_data), default=0) + 1
    record = {"ID": new_id}
    for (name, _), value in zip(schema, values):
        record[name] = value
    table_data.append(record)
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
    return table_data


def matches(record, where_clause):
    """Подходит ли запись под все условия where."""
    return all(record.get(column) == value for column, value in where_clause.items())


def select(table_data, where_clause=None):
    """Все записи или только подходящие под where_clause."""
    if where_clause is None:
        return table_data
    return [record for record in table_data if matches(record, where_clause)]


def update(table_data, set_clause, where_clause):
    """Обновляет поля set_clause в записях, подходящих под where_clause."""
    for record in table_data:
        if matches(record, where_clause):
            record.update(set_clause)
    return table_data


def delete(table_data, where_clause):
    """Удаляет записи, подходящие под where_clause."""
    return [record for record in table_data if not matches(record, where_clause)]
