from primitive_db.constants import (
    COLUMN_TYPE_SEPARATOR,
    ID_COLUMN,
    ID_TYPE,
    VALID_TYPES,
)
from primitive_db.decorators import confirm_action, handle_db_errors, log_time
from primitive_db.utils import load_table_data


def check_type(value, type_name):
    """Проверяет тип значения. bool и int различаются строго."""
    return type(value) is VALID_TYPES[type_name]


def ensure_table(metadata, table_name):
    """Бросает KeyError, если таблицы нет."""
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создаёт таблицу со столбцом ID:int в начале. Возвращает метаданные."""
    if table_name in metadata:
        raise ValueError(f'Ошибка: Таблица "{table_name}" уже существует.')

    table_columns = {ID_COLUMN: ID_TYPE}
    for column in columns:
        name, separator, column_type = column.partition(COLUMN_TYPE_SEPARATOR)
        if not separator or not name or column_type not in VALID_TYPES:
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")
        if name == ID_COLUMN and column_type == ID_TYPE:
            continue  # ID задан пользователем явно — он уже есть
        if name in table_columns:
            raise ValueError(f"Некорректное значение: {column}. Столбец уже указан.")
        table_columns[name] = column_type

    metadata[table_name] = {"columns": table_columns}
    columns_text = ", ".join(
        f"{name}{COLUMN_TYPE_SEPARATOR}{kind}" for name, kind in table_columns.items()
    )
    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_text}')
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных. Возвращает метаданные."""
    ensure_table(metadata, table_name)
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


def validate_clause(metadata, table_name, clause):
    """Проверяет, что столбцы условия существуют, а значения нужного типа."""
    ensure_table(metadata, table_name)
    columns = metadata[table_name]["columns"]
    for column, value in clause.items():
        if column not in columns:
            raise KeyError(f'Столбца "{column}" нет в таблице "{table_name}".')
        if not check_type(value, columns[column]):
            raise ValueError(f"Некорректное значение: {value}. Попробуйте снова.")


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Добавляет запись с автоматическим ID. Возвращает данные таблицы."""
    ensure_table(metadata, table_name)
    schema = [
        (name, kind)
        for name, kind in metadata[table_name]["columns"].items()
        if name != ID_COLUMN
    ]
    if len(values) != len(schema):
        raise ValueError(
            f"Некорректное значение: ожидается {len(schema)} значений, "
            f"получено {len(values)}. Попробуйте снова."
        )
    for (name, kind), value in zip(schema, values):
        if not check_type(value, kind):
            raise ValueError(
                f"Некорректное значение: {value}. Столбец {name} имеет тип {kind}."
            )

    table_data = load_table_data(table_name)
    new_id = max((record[ID_COLUMN] for record in table_data), default=0) + 1
    record = {ID_COLUMN: new_id}
    for (name, _), value in zip(schema, values):
        record[name] = value
    table_data.append(record)
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
    return table_data


def matches(record, where_clause):
    """Подходит ли запись под все условия where."""
    return all(record.get(column) == value for column, value in where_clause.items())


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Все записи или только подходящие под where_clause."""
    if where_clause is None:
        return table_data
    return [record for record in table_data if matches(record, where_clause)]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет поля set_clause в записях, подходящих под where_clause."""
    for record in table_data:
        if matches(record, where_clause):
            record.update(set_clause)
    return table_data


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Удаляет записи, подходящие под where_clause."""
    return [record for record in table_data if not matches(record, where_clause)]
