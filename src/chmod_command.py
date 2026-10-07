"""Команда chmod: изменение прав доступа узлов VFS в памяти."""

import re

import fs_commands
import vfs
from session import STATUS_ERROR, STATUS_OK

OCTAL_PATTERN = re.compile(r"[0-7]{1,4}")
CLAUSE_PATTERN = re.compile(r"([ugoa]*)([-+=])([rwx]*)")
ALL_BITS = 0o777
WHO_SHIFT = {"u": 6, "g": 3, "o": 0}
PERM_BITS = {"r": 4, "w": 2, "x": 1}
RECURSIVE_FLAGS = ("-R", "--recursive")


class ModeError(Exception):
    """Неверная запись режима."""


def clause_mask(who, perms):
    """Маски (права, затрагиваемые разряды) для одного выражения."""
    who = who or "a"
    shifts = [WHO_SHIFT[letter] for letter in "ugo"
              if "a" in who or letter in who]
    perm = sum(PERM_BITS[letter] for letter in set(perms))
    return (sum(perm << shift for shift in shifts),
            sum(0o7 << shift for shift in shifts))


def apply_clause(mode, clause):
    """Применить одно выражение вида u+x, go-w или a=r к правам."""
    match = CLAUSE_PATTERN.fullmatch(clause)
    if match is None:
        raise ModeError(clause)
    who, action, perms = match.groups()
    bits, scope = clause_mask(who, perms)
    if action == "+":
        return mode | bits
    if action == "-":
        return mode & ~bits
    return (mode & ~scope) | bits


def new_mode(spec, old_mode):
    """Вычислить новые права по записи режима (восьмеричной или u+x)."""
    if OCTAL_PATTERN.fullmatch(spec):
        return int(spec, vfs.OCTAL_BASE) & ALL_BITS
    mode = old_mode
    for clause in spec.split(","):
        mode = apply_clause(mode, clause)
    return mode & ALL_BITS


def split_args(args):
    """Выделить флаг -R, режим и операнды: (рекурсивно, режим, пути)."""
    args = list(args)
    recursive = False
    while args and args[0] in RECURSIVE_FLAGS:
        recursive = True
        args.pop(0)
    if args and args[0] == "--":
        args.pop(0)
    return recursive, (args[0] if args else None), args[1:]


def change_tree(node, label, spec, recursive):
    """Изменить права узла (и потомков при -R); вернуть статус."""
    node.mode = new_mode(spec, node.mode)
    if not recursive or isinstance(node, vfs.File):
        return STATUS_OK
    if not vfs.can_read(node):
        print(f"chmod: невозможно открыть каталог '{label}': "
              f"{fs_commands.MSG_DENIED}")
        return STATUS_ERROR
    status = STATUS_OK
    for name in sorted(node.children):
        child_label = vfs.child_label(label, name)
        if change_tree(node.children[name], child_label, spec, recursive):
            status = STATUS_ERROR
    return status


def cmd_chmod(session, args):
    """chmod [-R] режим путь...: режим — 644, u+x, go-w, a=rx."""
    recursive, spec, paths = split_args(args)
    if spec is None:
        print("chmod: пропущен операнд")
        return STATUS_ERROR
    if not paths:
        print(f"chmod: после '{spec}' пропущен операнд")
        return STATUS_ERROR
    try:
        new_mode(spec, 0)
    except ModeError:
        print(f"chmod: неверный режим: '{spec}'")
        return STATUS_ERROR
    status = STATUS_OK
    for label in paths:
        node = fs_commands.locate(session, label)[1]
        if node is None:
            print(f"chmod: невозможно получить доступ к '{label}': "
                  f"{fs_commands.MSG_NOT_FOUND}")
            status = STATUS_ERROR
        elif change_tree(node, label, spec, recursive):
            status = STATUS_ERROR
    return status
