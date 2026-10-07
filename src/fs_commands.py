"""Команды работы с VFS: ls, cd, du, find."""

import fnmatch

import vfs
from options import UsageError, split_options
from session import STATUS_ERROR, STATUS_OK

MSG_NOT_FOUND = "Нет такого файла или каталога"
MSG_DENIED = "Отказано в доступе"
KILOBYTE = 1024
SIZE_UNITS = "BKMGT"


def parse_options(name, args, allowed):
    """Разобрать опции; при ошибке напечатать её и вернуть None."""
    try:
        return split_options(args, allowed)
    except UsageError as err:
        print(f"{name}: {err}")
        return None


def locate(session, path):
    """Найти узел по пути пользователя: (список имён, узел или None)."""
    parts = vfs.resolve(session.cwd, path)
    return parts, vfs.lookup(session.root, parts)


def format_entry(node, label, long_format):
    """Строка вывода ls для одной записи."""
    if not long_format:
        return label
    size = vfs.entry_size(node)
    return f"{vfs.mode_string(node)} {size:>6} {label}"


def split_operands(session, operands):
    """Разложить операнды ls на файлы и каталоги; считать ошибки."""
    files, dirs, status = [], [], STATUS_OK
    for label in operands:
        node = locate(session, label)[1]
        if node is None:
            print(f"ls: невозможно получить доступ к '{label}': "
                  f"{MSG_NOT_FOUND}")
            status = STATUS_ERROR
        elif isinstance(node, vfs.Dir):
            dirs.append((label, node))
        else:
            files.append((label, node))
    return files, dirs, status


def print_dir(label, node, flags, header):
    """Вывести содержимое каталога; вернуть статус."""
    if header:
        print(f"{label}:")
    if not vfs.can_read(node):
        print(f"ls: невозможно открыть каталог '{label}': {MSG_DENIED}")
        return STATUS_ERROR
    for name in sorted(node.children):
        if name.startswith(".") and "a" not in flags:
            continue
        print(format_entry(node.children[name], name, "l" in flags))
    return STATUS_OK


def cmd_ls(session, args):
    """ls [-a] [-l] [путь...]: содержимое каталогов и информация о файлах."""
    parsed = parse_options("ls", args, "al")
    if parsed is None:
        return STATUS_ERROR
    flags, operands = parsed
    files, dirs, status = split_operands(session, operands or ["."])
    for label, node in files:
        print(format_entry(node, label, "l" in flags))
    for index, (label, node) in enumerate(dirs):
        if index or files:
            print()
        if print_dir(label, node, flags, len(operands) > 1):
            status = STATUS_ERROR
    return status


def cmd_cd(session, args):
    """cd [путь]: перейти в каталог; без аргумента — в корень VFS."""
    if len(args) > 1:
        print("cd: слишком много аргументов")
        return STATUS_ERROR
    path = args[0] if args else "/"
    parts, node = locate(session, path)
    if node is None:
        print(f"cd: {path}: {MSG_NOT_FOUND}")
    elif not isinstance(node, vfs.Dir):
        print(f"cd: {path}: Не каталог")
    elif not vfs.can_enter(node):
        print(f"cd: {path}: {MSG_DENIED}")
    else:
        session.cwd = parts
        return STATUS_OK
    return STATUS_ERROR


def human_size(size):
    """Размер в удобном виде: 512B, 1.5K, 2.0M."""
    value = float(size)
    unit = 0
    while value >= KILOBYTE and unit < len(SIZE_UNITS) - 1:
        value /= KILOBYTE
        unit += 1
    if unit == 0:
        return f"{size}B"
    return f"{value:.1f}{SIZE_UNITS[unit]}"


def du_collect(node, label, flags, report):
    """Посчитать размер узла; report накапливает (размер, путь, ошибка)."""
    if isinstance(node, vfs.File):
        if "a" in flags:
            report.append((node.size, label, False))
        return node.size
    total, denied = 0, not vfs.can_read(node)
    if not denied:
        for name in sorted(node.children):
            child = node.children[name]
            total += du_collect(child, vfs.child_label(label, name),
                                flags, report)
    report.append((total, label, denied))
    return total


def du_operand(session, label, flags):
    """Обработать один операнд du; вернуть статус."""
    node = locate(session, label)[1]
    if node is None:
        print(f"du: невозможно получить доступ к '{label}': "
              f"{MSG_NOT_FOUND}")
        return STATUS_ERROR
    report = []
    total = du_collect(node, label, flags, report)
    if "s" in flags or not report:
        report = report[-1:] or [(total, label, False)]
    status = STATUS_OK
    for size, path, denied in report:
        shown = human_size(size) if "h" in flags else str(size)
        print(f"{shown}\t{path}")
        if denied:
            print(f"du: невозможно прочитать каталог '{path}': {MSG_DENIED}")
            status = STATUS_ERROR
    return status


def cmd_du(session, args):
    """du [-a] [-s] [-h] [путь...]: размер файлов в байтах."""
    parsed = parse_options("du", args, "ash")
    if parsed is None:
        return STATUS_ERROR
    flags, operands = parsed
    status = STATUS_OK
    for label in operands or ["."]:
        if du_operand(session, label, flags):
            status = STATUS_ERROR
    return status


def parse_find(args):
    """Разобрать аргументы find: (пути, шаблон имени, тип)."""
    paths = []
    while args and not args[0].startswith("-"):
        paths.append(args.pop(0))
    criteria = {"-name": None, "-type": None}
    while args:
        key = args.pop(0)
        if key not in criteria:
            raise UsageError(f"неизвестный предикат '{key}'")
        if not args:
            raise UsageError(f"отсутствует аргумент для '{key}'")
        criteria[key] = args.pop(0)
    if criteria["-type"] not in (None, "f", "d"):
        raise UsageError(f"неизвестный тип '{criteria['-type']}'")
    return paths or ["."], criteria["-name"], criteria["-type"]


def find_matches(node, label, pattern, kind):
    """Проверить узел на соответствие -name и -type."""
    name = label.rstrip("/").rsplit("/", 1)[-1] or "/"
    if pattern is not None and not fnmatch.fnmatchcase(name, pattern):
        return False
    if kind == "f":
        return isinstance(node, vfs.File)
    return kind != "d" or isinstance(node, vfs.Dir)


def find_walk(node, label, criteria, errors):
    """Обойти дерево, печатая подходящие узлы (в прямом порядке)."""
    pattern, kind = criteria
    if find_matches(node, label, pattern, kind):
        print(label)
    if not isinstance(node, vfs.Dir):
        return
    if not vfs.can_read(node):
        print(f"find: '{label}': {MSG_DENIED}")
        errors.append(label)
        return
    for name in sorted(node.children):
        find_walk(node.children[name], vfs.child_label(label, name),
                  criteria, errors)


def cmd_find(session, args):
    """find [путь...] [-name шаблон] [-type f|d]: поиск по дереву VFS."""
    try:
        paths, pattern, kind = parse_find(list(args))
    except UsageError as err:
        print(f"find: {err}")
        return STATUS_ERROR
    errors = []
    for label in paths:
        node = locate(session, label)[1]
        if node is None:
            print(f"find: '{label}': {MSG_NOT_FOUND}")
            errors.append(label)
        else:
            find_walk(node, label, (pattern, kind), errors)
    return STATUS_ERROR if errors else STATUS_OK
