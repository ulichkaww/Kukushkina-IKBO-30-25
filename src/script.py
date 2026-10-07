"""Выполнение стартового скрипта эмулятора."""

from session import STATUS_ERROR, STATUS_OK

COMMENT_PREFIX = "#"


class ScriptReadError(Exception):
    """Скрипт не удалось прочитать."""


def read_script(path):
    """Прочитать строки скрипта."""
    try:
        with open(path, encoding="utf-8") as file:
            return file.read().splitlines()
    except FileNotFoundError as err:
        raise ScriptReadError(f"файл скрипта не найден: {path}") from err
    except (OSError, UnicodeDecodeError) as err:
        raise ScriptReadError(f"не удалось прочитать {path}: {err}") from err


def run_script(session, path, execute):
    """Выполнить скрипт, имитируя диалог; остановиться на первой ошибке.

    execute(session, line) возвращает статус команды.
    """
    for number, raw in enumerate(read_script(path), start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT_PREFIX):
            continue
        print(session.prompt() + line)
        if execute(session, line) != STATUS_OK:
            print(f"Ошибка выполнения скрипта {path}, строка {number}: "
                  f"{line}")
            return STATUS_ERROR
        if not session.running:
            break
    return STATUS_OK
