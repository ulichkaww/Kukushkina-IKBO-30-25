"""Разбор введённой строки: токены и переменные окружения."""

import os
import re
import shlex

ENV_PATTERN = re.compile(r"\$(\w+)|\$\{(\w+)\}")


class ParseError(Exception):
    """Строка не может быть разобрана."""


def expand_env(text):
    """Подставить значения переменных окружения реальной ОС.

    Неизвестная переменная заменяется пустой строкой, как в shell.
    """
    def replace(match):
        """Значение переменной для одного совпадения."""
        name = match.group(1) or match.group(2)
        return os.environ.get(name, "")

    return ENV_PATTERN.sub(replace, text)


def parse_line(line):
    """Разбить строку на токены (с кавычками) и раскрыть $VAR."""
    try:
        tokens = shlex.split(line)
    except ValueError as err:
        raise ParseError(f"ошибка разбора: {err}") from err
    return [expand_env(token) for token in tokens]
