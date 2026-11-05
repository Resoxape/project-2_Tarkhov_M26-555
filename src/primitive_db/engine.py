import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import (
    COLUMN_TYPE_SEPARATOR,
    ID_COLUMN,
    META_FILE,
    PROMPT_TEXT,
)
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
from primitive_db.parser import (
    incorrect,
    parse_delete,
    parse_info,
    parse_insert,
    parse_select,
    parse_update,
)
from primitive_db.utils import (
    data_version,
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

select_cache = create_cacher()


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


def matching_ids(table_data, where_clause):
    """ID записей, подходящих под условие where."""
    return [record[ID_COLUMN] for record in table_data if matches(record, where_clause)]


@handle_db_errors
def handle_table_command(metadata, command, user_input):
    """Обрабатывает create_table, drop_table и list_tables."""
    try:
        _, *params = shlex.split(user_input)
    except ValueError:
        raise incorrect(user_input) from None

    match command:
        case "create_table":
            if not params:
                raise incorrect(user_input)
            if create_table(metadata, params[0], params[1:]) is not None:
                save_metadata(META_FILE, metadata)
        case "drop_table":
            if len(params) != 1:
                raise incorrect(user_input)
            if not table_exists(metadata, params[0]):
                return
            if drop_table(metadata, params[0]) is not None:
                save_metadata(META_FILE, metadata)
                delete_table_data(params[0])
        case "list_tables":
            list_tables(metadata)


@handle_db_errors
def handle_insert(metadata, user_input):
    """Обрабатывает insert into ... values (...)."""
    table_name, values = parse_insert(user_input)
    table_data = insert(metadata, table_name, values)
    if table_data is not None:
        save_table_data(table_name, table_data)


@handle_db_errors
def handle_select(metadata, user_input):
    """Обрабатывает select from ... [where ...] с кэшированием результата."""
    table_name, where_clause = parse_select(user_input)
    if not table_exists(metadata, table_name):
        return
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
    """Обрабатывает update ... set ... where ...."""
    table_name, set_clause, where_clause = parse_update(user_input)
    if not table_exists(metadata, table_name):
        return
    if ID_COLUMN in set_clause:
        print(f"Ошибка: столбец {ID_COLUMN} изменять нельзя.")
        return
    validate_clause(metadata, table_name, set_clause)
    validate_clause(metadata, table_name, where_clause)

    table_data = load_table_data(table_name)
    ids = matching_ids(table_data, where_clause)
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
    """Обрабатывает delete from ... where ... (с подтверждением)."""
    table_name, where_clause = parse_delete(user_input)
    if not table_exists(metadata, table_name):
        return
    validate_clause(metadata, table_name, where_clause)

    table_data = load_table_data(table_name)
    ids = matching_ids(table_data, where_clause)
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
    """Обрабатывает info <таблица>."""
    table_name = parse_info(user_input)
    if not table_exists(metadata, table_name):
        return
    columns = metadata[table_name]["columns"]
    columns_text = ", ".join(
        f"{name}{COLUMN_TYPE_SEPARATOR}{kind}" for name, kind in columns.items()
    )
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
            user_input = prompt.string(PROMPT_TEXT).strip()
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
