import re
import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    matches,
    select,
    update,
    validate_clause,
)
from primitive_db.decorators import create_cacher, handle_db_errors
from primitive_db.parser import parse_set, parse_values, parse_where
from primitive_db.utils import (
    data_version,
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

META_FILE = "db_meta.json"

select_cache = create_cacher()

INSERT_RE = re.compile(r"^insert\s+into\s+(\w+)\s+values\s*\((.*)\)$", re.IGNORECASE)
SELECT_RE = re.compile(r"^select\s+from\s+(\w+)(?:\s+where\s+(.+))?$", re.IGNORECASE)
UPDATE_RE = re.compile(r"^update\s+(\w+)\s+set\s+(.+?)\s+where\s+(.+)$", re.IGNORECASE)
DELETE_RE = re.compile(r"^delete\s+from\s+(\w+)\s+where\s+(.+)$", re.IGNORECASE)
INFO_RE = re.compile(r"^info\s+(\w+)$", re.IGNORECASE)


def print_help():
    """Prints the help message for the current mode."""

    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\n***Операции с данными***")
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>, ...) - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение> "
        "- прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1> "
        "where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> "
        "- удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def print_incorrect(value):
    """Сообщение о некорректном значении."""
    print(f"Некорректное значение: {value}. Попробуйте снова.")


def table_exists(metadata, table_name):
    """Проверяет наличие таблицы и выводит ошибку, если её нет."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return False
    return True


def print_records(columns, records):
    """Выводит записи таблицы через PrettyTable."""
    table = PrettyTable()
    table.field_names = list(columns)
    for record in records:
        table.add_row([record[column] for column in columns])
    print(table)


@handle_db_errors
def handle_table_command(metadata, command, user_input):
    """create_table / drop_table / list_tables."""
    try:
        _, *params = shlex.split(user_input)
    except ValueError:
        raise ValueError(
            f"Некорректное значение: {user_input}. Попробуйте снова."
        ) from None

    match command:
        case "create_table":
            if not params:
                print_incorrect(user_input)
                return
            if create_table(metadata, params[0], params[1:]) is not None:
                save_metadata(META_FILE, metadata)
        case "drop_table":
            if len(params) != 1:
                print_incorrect(user_input)
                return
            if not table_exists(metadata, params[0]):
                return
            if drop_table(metadata, params[0]) is not None:
                save_metadata(META_FILE, metadata)
                delete_table_data(params[0])
        case "list_tables":
            list_tables(metadata)


@handle_db_errors
def handle_insert(metadata, user_input):
    match_ = INSERT_RE.match(user_input)
    if not match_:
        print_incorrect(user_input)
        return
    table_name, raw_values = match_.groups()
    table_data = insert(metadata, table_name, parse_values(raw_values))
    if table_data is not None:
        save_table_data(table_name, table_data)


@handle_db_errors
def handle_select(metadata, user_input):
    match_ = SELECT_RE.match(user_input)
    if not match_:
        print_incorrect(user_input)
        return
    table_name, raw_where = match_.groups()
    if not table_exists(metadata, table_name):
        return
    where_clause = parse_where(raw_where) if raw_where else None
    if where_clause:
        validate_clause(metadata, table_name, where_clause)

    # Ключ кэша включает версию файла данных: после изменений кэш не устаревает.
    where_key = tuple(sorted(where_clause.items())) if where_clause else None
    cache_key = (table_name, data_version(table_name), where_key)
    records = select_cache(
        cache_key, lambda: select(load_table_data(table_name), where_clause)
    )
    if records is None:
        return
    if not records:
        print("Записи не найдены.")
        return
    print_records(metadata[table_name]["columns"], records)


@handle_db_errors
def handle_update(metadata, user_input):
    match_ = UPDATE_RE.match(user_input)
    if not match_:
        print_incorrect(user_input)
        return
    table_name, raw_set, raw_where = match_.groups()
    if not table_exists(metadata, table_name):
        return
    set_clause = parse_set(raw_set)
    where_clause = parse_where(raw_where)
    if "ID" in set_clause:
        print("Ошибка: столбец ID изменять нельзя.")
        return
    validate_clause(metadata, table_name, set_clause)
    validate_clause(metadata, table_name, where_clause)

    table_data = load_table_data(table_name)
    ids = [record["ID"] for record in table_data if matches(record, where_clause)]
    if not ids:
        print("Записи по условию не найдены.")
        return
    table_data = update(table_data, set_clause, where_clause)
    if table_data is None:
        return
    save_table_data(table_name, table_data)
    for record_id in ids:
        print(f'Запись с ID={record_id} в таблице "{table_name}" успешно обновлена.')


@handle_db_errors
def handle_delete(metadata, user_input):
    match_ = DELETE_RE.match(user_input)
    if not match_:
        print_incorrect(user_input)
        return
    table_name, raw_where = match_.groups()
    if not table_exists(metadata, table_name):
        return
    where_clause = parse_where(raw_where)
    validate_clause(metadata, table_name, where_clause)

    table_data = load_table_data(table_name)
    ids = [record["ID"] for record in table_data if matches(record, where_clause)]
    if not ids:
        print("Записи по условию не найдены.")
        return
    table_data = delete(table_data, where_clause)
    if table_data is None:
        return
    save_table_data(table_name, table_data)
    for record_id in ids:
        print(f'Запись с ID={record_id} успешно удалена из таблицы "{table_name}".')


@handle_db_errors
def handle_info(metadata, user_input):
    match_ = INFO_RE.match(user_input)
    if not match_:
        print_incorrect(user_input)
        return
    table_name = match_.group(1)
    if not table_exists(metadata, table_name):
        return
    columns = metadata[table_name]["columns"]
    columns_text = ", ".join(f"{name}:{kind}" for name, kind in columns.items())
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {columns_text}")
    print(f"Количество записей: {len(load_table_data(table_name))}")


def run():
    """Основной цикл программы: ввод, разбор и выполнение команд."""
    print("\n***База данных***")
    print_help()

    while True:
        metadata = load_metadata(META_FILE)

        try:
            user_input = prompt.string(">>>Введите команду: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not user_input:
            continue

        command = user_input.split()[0].lower()
        match command:
            case "create_table" | "drop_table" | "list_tables":
                handle_table_command(metadata, command, user_input)
            case "insert":
                handle_insert(metadata, user_input)
            case "select":
                handle_select(metadata, user_input)
            case "update":
                handle_update(metadata, user_input)
            case "delete":
                handle_delete(metadata, user_input)
            case "info":
                handle_info(metadata, user_input)
            case "help":
                print_help()
            case "exit":
                break
            case _:
                print(f"Функции {command} нет. Попробуйте снова.")
        print()
