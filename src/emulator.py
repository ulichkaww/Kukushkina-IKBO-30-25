"""Эмулятор командной строки UNIX-подобной ОС (вариант 16)."""

import os
import sys

import cmdline
import commands
import config
import script
import vfs
from session import STATUS_ERROR, STATUS_OK, Session

EXIT_CONFIG_ERROR = 2


def execute(session, line):
    """Выполнить одну строку и вернуть статус завершения."""
    try:
        tokens = cmdline.parse_line(line)
    except cmdline.ParseError as err:
        print(err)
        return STATUS_ERROR
    if not tokens:
        return STATUS_OK
    handler = commands.COMMANDS.get(tokens[0])
    if handler is None:
        print(f"{tokens[0]}: команда не найдена")
        return STATUS_ERROR
    return handler(session, tokens[1:])


def repl(session):
    """Диалог с пользователем: читать команды до exit или Ctrl+D."""
    while session.running:
        try:
            line = input(session.prompt())
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue
        execute(session, line)


def load_session(path):
    """Создать сеанс: VFS загружается из XML или создаётся пустой."""
    if not path:
        return Session()
    name, root = vfs.load_vfs(path)
    return Session(name, root)


def start(settings):
    """Создать сеанс, выполнить стартовый скрипт и запустить REPL."""
    try:
        session = load_session(settings.vfs)
    except vfs.VfsError as err:
        print(f"Ошибка загрузки VFS: {err}")
        return EXIT_CONFIG_ERROR
    if settings.script:
        try:
            status = script.run_script(session, settings.script, execute)
        except script.ScriptReadError as err:
            print(f"Ошибка стартового скрипта: {err}")
            return EXIT_CONFIG_ERROR
        if status != STATUS_OK:
            return status
    if session.running:
        repl(session)
    return STATUS_OK


def main(argv=None):
    """Точка входа: параметры, отладочный вывод, скрипт, диалог."""
    os.environ.setdefault("HOME", os.path.expanduser("~"))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = config.build_arg_parser().parse_args(argv)
    try:
        settings = config.load_settings(args)
    except config.ConfigError as err:
        print(f"Ошибка конфигурации: {err}")
        return EXIT_CONFIG_ERROR
    print("\n".join(config.describe(settings)))
    return start(settings)


if __name__ == "__main__":
    sys.exit(main())
