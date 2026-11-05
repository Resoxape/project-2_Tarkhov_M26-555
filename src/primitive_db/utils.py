import json
import os

from primitive_db.constants import (
    DATA_DIR,
    DATA_FILE_EXTENSION,
    FILE_ENCODING,
    JSON_INDENT,
)


def load_metadata(filepath):
    """Загружает метаданные из JSON-файла. Если файла нет, возвращает {}."""
    try:
        with open(filepath, encoding=FILE_ENCODING) as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка: файл {filepath} повреждён, метаданные сброшены.")
        return {}


def save_metadata(filepath, data):
    """Сохраняет метаданные в JSON-файл."""
    with open(filepath, "w", encoding=FILE_ENCODING) as file:
        json.dump(data, file, ensure_ascii=False, indent=JSON_INDENT)


def table_path(table_name):
    """Путь к файлу с данными таблицы: data/<имя_таблицы>.json."""
    return os.path.join(DATA_DIR, f"{table_name}{DATA_FILE_EXTENSION}")


def load_table_data(table_name):
    """Загружает записи таблицы. Если файла нет, возвращает []."""
    try:
        with open(table_path(table_name), encoding=FILE_ENCODING) as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Ошибка: данные таблицы {table_name} повреждены, таблица пуста.")
        return []


def save_table_data(table_name, data):
    """Сохраняет записи таблицы в data/<имя_таблицы>.json."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(table_path(table_name), "w", encoding=FILE_ENCODING) as file:
        json.dump(data, file, ensure_ascii=False, indent=JSON_INDENT)


def delete_table_data(table_name):
    """Удаляет файл с данными таблицы, если он есть."""
    try:
        os.remove(table_path(table_name))
    except FileNotFoundError:
        pass


def data_version(table_name):
    """Версия данных таблицы — время изменения файла (0, если файла нет)."""
    try:
        return os.stat(table_path(table_name)).st_mtime_ns
    except FileNotFoundError:
        return 0
