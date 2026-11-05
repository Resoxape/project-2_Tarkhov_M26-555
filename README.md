# primitive_db

Учебный проект: консольное приложение, имитирующее работу с базой данных.

## Запуск

```
uv sync
uv run database
```

## Демонстрация

Установка пакета, запуск БД, создание, проверка и удаление таблицы:

[![asciicast](https://asciinema.org/a/BxeFn5JAPpJx56Ek.svg)](https://asciinema.org/a/BxeFn5JAPpJx56Ek)

## Установка

```
uv build
uv tool install dist/primitive_db-0.2.0-py3-none-any.whl
database
```

## Управление таблицами

Метаданные таблиц (имена и столбцы с типами) хранятся в файле `db_meta.json`
в текущей директории. Поддерживаемые типы данных: `int`, `str`, `bool`.
Столбец `ID:int` добавляется в начало каждой таблицы автоматически.

| Команда | Описание |
|---|---|
| `create_table <имя> <столбец:тип> ...` | создать таблицу |
| `list_tables` | показать список всех таблиц |
| `drop_table <имя>` | удалить таблицу |
| `help` | справочная информация |
| `exit` | выход из программы |

### Пример

```
>>>Введите команду: create_table users name:str age:int is_active:bool
Таблица "users" успешно создана со столбцами: ID:int, name:str, age:int, is_active:bool

>>>Введите команду: list_tables
- users

>>>Введите команду: drop_table users
Таблица "users" успешно удалена.

>>>Введите команду: drop_table products
Ошибка: Таблица "products" не существует.
```
