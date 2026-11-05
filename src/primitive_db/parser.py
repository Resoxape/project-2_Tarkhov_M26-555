import re

IDENTIFIER = re.compile(r"^[A-Za-z_]\w*$")
INTEGER = re.compile(r"^-?\d+$")
QUOTES = "\"'"


def parse_value(raw):
    """Превращает текст значения в int, bool или str (строки только в кавычках)."""
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in QUOTES:
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if INTEGER.match(value):
        return int(value)
    raise ValueError(value)


def split_outside_quotes(text, separator=","):
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
        raise ValueError(text.strip())
    parts.append("".join(current))
    return parts


def parse_values(text):
    """'"Sergei", 28, true' -> ['Sergei', 28, True]."""
    if not text.strip():
        return []
    return [parse_value(part) for part in split_outside_quotes(text)]


def parse_condition(text):
    """'age = 28' -> {'age': 28}."""
    column, separator, raw_value = text.partition("=")
    column = column.strip()
    if not separator or not IDENTIFIER.match(column):
        raise ValueError(text.strip())
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
