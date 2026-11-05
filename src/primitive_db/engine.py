import shlex

import prompt

from primitive_db.core import create_table, drop_table, list_tables
from primitive_db.utils import load_metadata, save_metadata

META_FILE = "db_meta.json"


def print_help():
    """Prints the help message for the current mode."""

    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def run():
    """Основной цикл программы: ввод, разбор и выполнение команд."""
    print("\n***База данных***")
    print_help()

    while True:
        metadata = load_metadata(META_FILE)

        try:
            user_input = prompt.string(">>>Введите команду: ")
        except (KeyboardInterrupt, EOFError):
            print()
            break

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue
        if not args:
            continue

        command, *params = args
        match command:
            case "create_table":
                if not params:
                    print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                    continue
                metadata = create_table(metadata, params[0], params[1:])
                save_metadata(META_FILE, metadata)
            case "drop_table":
                if len(params) != 1:
                    print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                    continue
                metadata = drop_table(metadata, params[0])
                save_metadata(META_FILE, metadata)
            case "list_tables":
                list_tables(metadata)
            case "help":
                print_help()
            case "exit":
                break
            case _:
                print(f"Функции {command} нет. Попробуйте снова.")
        print()
