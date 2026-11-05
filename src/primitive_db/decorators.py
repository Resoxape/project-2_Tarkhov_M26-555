import time

from primitive_db.constants import CONFIRM_YES


def keep_name(wrapper, func):
    """Переносит имя и docstring исходной функции на обёртку."""
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def handle_db_errors(func):
    """Перехватывает ошибки операций с БД и выводит понятное сообщение."""

    def wrapper(*args, **kwargs):
        """Вызывает функцию внутри try...except."""
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as error:
            print(f"Ошибка: {error.args[0]}")
        except ValueError as error:
            print(error)
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")
        return None

    return keep_name(wrapper, func)


def confirm_action(action_name):
    """Фабрика декораторов: запрашивает подтверждение опасной операции."""

    def decorator(func):
        """Оборачивает функцию запросом подтверждения."""

        def wrapper(*args, **kwargs):
            """Выполняет функцию, только если пользователь ответил 'y'."""
            answer = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')
            if answer.strip().lower() != CONFIRM_YES:
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return keep_name(wrapper, func)

    return decorator


def log_time(func):
    """Замеряет и выводит время выполнения функции."""

    def wrapper(*args, **kwargs):
        """Вызывает функцию и печатает, сколько секунд она выполнялась."""
        start = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start
        print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")
        return result

    return keep_name(wrapper, func)


def create_cacher():
    """Возвращает функцию cache_result, хранящую кэш в замыкании."""
    cache = {}

    def cache_result(key, value_func):
        """Возвращает результат из кэша или вычисляет и запоминает его."""
        if key in cache:
            return cache[key]
        result = value_func()
        cache[key] = result
        return result

    return cache_result
