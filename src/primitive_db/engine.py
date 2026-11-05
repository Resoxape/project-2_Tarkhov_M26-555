import prompt

HELP_TEXT = (
    "<command> exit - выйти из программы\n<command> help - справочная информация"
)


def print_help():
    """Выводит справку по доступным командам."""
    print(HELP_TEXT)


def welcome():
    """Приветствие и основной цикл обработки команд."""
    print("Первая попытка запустить проект!")
    print()
    print("***")
    print_help()
    while True:
        command = prompt.string("Введите команду: ").strip()
        match command:
            case "exit":
                break
            case "help":
                print()
                print_help()
            case _:
                print(f"Неизвестная команда: {command}. Введите help для справки.")
