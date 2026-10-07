"""Разбор коротких опций команд (-l, -la, --)."""


class UsageError(Exception):
    """Неверные опции или аргументы команды."""


def split_options(args, allowed):
    """Разделить аргументы на набор флагов и операнды.

    allowed — строка допустимых однобуквенных опций. Опции можно
    склеивать (-la); '--' заканчивает список опций.
    """
    flags = set()
    operands = []
    options_done = False
    for arg in args:
        if options_done or arg == "-" or not arg.startswith("-"):
            operands.append(arg)
        elif arg == "--":
            options_done = True
        elif arg.startswith("--"):
            raise UsageError(f"неизвестная опция '{arg}'")
        else:
            flags.update(check_letters(arg[1:], allowed))
    return flags, operands


def check_letters(letters, allowed):
    """Проверить буквы склеенных опций."""
    for letter in letters:
        if letter not in allowed:
            raise UsageError(f"неизвестная опция -- '{letter}'")
    return letters
