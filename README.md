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
uv tool install dist/primitive_db-0.3.0-py3-none-any.whl
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

## CRUD-операции

Данные каждой таблицы хранятся в отдельном файле `data/<имя_таблицы>.json`.
Строковые значения всегда пишутся в кавычках, `bool` — как `true`/`false`.
`ID` генерируется автоматически и в `insert` не передаётся; все поля обязательны.

| Команда | Описание |
|---|---|
| `insert into <таблица> values (<значение1>, <значение2>, ...)` | создать запись |
| `select from <таблица>` | прочитать все записи |
| `select from <таблица> where <столбец> = <значение>` | прочитать записи по условию |
| `update <таблица> set <столбец> = <значение> where <столбец> = <значение>` | обновить записи |
| `delete from <таблица> where <столбец> = <значение>` | удалить записи |
| `info <таблица>` | информация о таблице |

### Пример

```
>>>Введите команду: insert into users values ("Sergei", 28, true)
Запись с ID=1 успешно добавлена в таблицу "users".

>>>Введите команду: select from users where age = 28
+----+--------+-----+-----------+
| ID |  name  | age | is_active |
+----+--------+-----+-----------+
| 1  | Sergei |  28 |    True   |
+----+--------+-----+-----------+

>>>Введите команду: update users set age = 29 where name = "Sergei"
Запись с ID=1 в таблице "users" успешно обновлена.

>>>Введите команду: delete from users where ID = 1
Запись с ID=1 успешно удалена из таблицы "users".

>>>Введите команду: info users
Таблица: users
Столбцы: ID:int, name:str, age:int, is_active:bool
Количество записей: 0
```

### Демонстрация CRUD

[![asciicast](https://asciinema.org/a/IFWj6pg9Dy4gpE0t.svg)](https://asciinema.org/a/IFWj6pg9Dy4gpE0t)
