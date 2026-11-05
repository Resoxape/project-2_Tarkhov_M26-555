from primitive_db.constants import (
    ASSIGNMENT,
    DIGITS,
    FALSE_LITERAL,
    QUOTES,
    TRUE_LITERAL,
    VALUES_SEPARATOR,
)


def incorrect(value):
    """Создаёт ValueError со стандартным сообщением о некорректном значении."""
    return ValueError(f"Некорректное значение: {value}. Попробуйте снова.")


def is_integer(text):
    """Проверяет, что строка — целое число (возможно, со знаком минус)."""
    digits = text[1:] if text.startswith("-") else text
    return bool(digits) and all(char in DIGITS for char in digits)


def parse_value(raw):
    """Превращает текст значения в int, bool или str (строки только в кавычках)."""
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in QUOTES:
        return value[1:-1]
    if value.lower() == TRUE_LITERAL:
        return True
    if value.lower() == FALSE_LITERAL:
        return False
    if is_integer(value):
        return int(value)
    raise incorrect(value)


def split_outside_quotes(text, separator=VALUES_SEPARATOR):
    """Делит строку по разделителю, не трогая разделители внутри кавычек."""
    parts = []
    current = []
    quote = None
    for char in text:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
        elif char in QUOTES:
            quote = char
            current.append(char)
        elif char == separator:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    if quote:
        raise incorrect(text.strip())
    parts.append("".join(current))
    return parts


def parse_values(text):
    """'"Sergei", 28, true' -> ['Sergei', 28, True]."""
    if not text.strip():
        return []
    return [parse_value(part) for part in split_outside_quotes(text)]


def parse_condition(text):
    """'age = 28' -> {'age': 28}."""
    column, separator, raw_value = text.partition(ASSIGNMENT)
    column = column.strip()
    if not separator or not column.isidentifier() or not raw_value.strip():
        raise incorrect(text.strip())
    return {column: parse_value(raw_value)}


def parse_where(text):
    """Условие where: 'name = "Sergei"' -> {'name': 'Sergei'}."""
    return parse_condition(text)


def parse_set(text):
    """Условие set: 'age = 29, is_active = false' -> {'age': 29, 'is_active': False}."""
    result = {}
    for part in split_outside_quotes(text):
        result.update(parse_condition(part))
    return result


def is_word_boundary(text, index):
    """True, если позиция index — граница слова (конец строки или не буква/цифра)."""
    return index >= len(text) or not (text[index].isalnum() or text[index] == "_")


def find_keyword(text, keyword):
    """Ищет ключевое слово отдельным словом вне кавычек. Возвращает индекс или -1."""
    lowered = text.lower()
    quote = None
    for index, char in enumerate(text):
        if quote:
            if char == quote:
                quote = None
            continue
        if char in QUOTES:
            quote = char
            continue
        if (
            lowered.startswith(keyword, index)
            and (index == 0 or text[index - 1].isspace())
            and is_word_boundary(text, index + len(keyword))
        ):
            return index
    return -1


def take_keyword(text, keyword, user_input):
    """Отрезает ключевое слово в начале строки и возвращает остаток."""
    text = text.strip()
    if not text.lower().startswith(keyword) or not is_word_boundary(text, len(keyword)):
        raise incorrect(user_input)
    return text[len(keyword) :].strip()


def take_name(text, user_input):
    """Отрезает имя (таблицы) в начале строки. Возвращает (имя, остаток)."""
    parts = text.split(maxsplit=1)
    if not parts or not parts[0].isidentifier():
        raise incorrect(user_input)
    return parts[0], parts[1] if len(parts) > 1 else ""


def parse_insert(user_input):
    """insert into <таблица> values (...) -> (таблица, [значения])."""
    rest = take_keyword(user_input, "insert", user_input)
    rest = take_keyword(rest, "into", user_input)
    table_name, rest = take_name(rest, user_input)
    rest = take_keyword(rest, "values", user_input)
    if not (rest.startswith("(") and rest.endswith(")")):
        raise incorrect(user_input)
    return table_name, parse_values(rest[1:-1])


def parse_select(user_input):
    """select from <таблица> [where ...] -> (таблица, where или None)."""
    rest = take_keyword(user_input, "select", user_input)
    rest = take_keyword(rest, "from", user_input)
    table_name, rest = take_name(rest, user_input)
    if not rest:
        return table_name, None
    rest = take_keyword(rest, "where", user_input)
    if not rest:
        raise incorrect(user_input)
    return table_name, parse_where(rest)


def parse_update(user_input):
    """update <таблица> set ... where ... -> (таблица, set, where)."""
    rest = take_keyword(user_input, "update", user_input)
    table_name, rest = take_name(rest, user_input)
    rest = take_keyword(rest, "set", user_input)
    where_index = find_keyword(rest, "where")
    if where_index == -1:
        raise incorrect(user_input)
    set_part = rest[:where_index]
    where_part = rest[where_index + len("where") :]
    if not set_part.strip() or not where_part.strip():
        raise incorrect(user_input)
    return table_name, parse_set(set_part), parse_where(where_part)


def parse_delete(user_input):
    """delete from <таблица> where ... -> (таблица, where)."""
    rest = take_keyword(user_input, "delete", user_input)
    rest = take_keyword(rest, "from", user_input)
    table_name, rest = take_name(rest, user_input)
    rest = take_keyword(rest, "where", user_input)
    if not rest:
        raise incorrect(user_input)
    return table_name, parse_where(rest)


def parse_info(user_input):
    """info <таблица> -> таблица."""
    rest = take_keyword(user_input, "info", user_input)
    table_name, rest = take_name(rest, user_input)
    if rest:
        raise incorrect(user_input)
    return table_name
