"""Реестр команд эмулятора, exit и служебная команда vfs-info."""

import chmod_command
import fs_commands
import vfs
from session import STATUS_ERROR, STATUS_OK


def describe_node(node):
    """Строка описания узла для vfs-info."""
    if isinstance(node, vfs.Dir):
        return f"{node.name}/ [{node.mode:03o}]"
    return f"{node.name} [{node.mode:03o}] {node.size} байт"


def cmd_vfs_info(session, args):
    """Служебная команда: сводка и дерево загруженной VFS."""
    if args:
        print("vfs-info: команда не принимает аргументов")
        return STATUS_ERROR
    nodes = list(vfs.walk(session.root))
    files = [node for _, node in nodes if isinstance(node, vfs.File)]
    print(f"VFS '{session.vfs_name}': "
          f"{len(nodes) - len(files)} каталогов, {len(files)} файлов")
    for depth, node in nodes:
        print("  " * (depth + 1) + describe_node(node))
    return STATUS_OK


def cmd_exit(session, args):
    """Завершить работу эмулятора."""
    if args:
        print("exit: команда не принимает аргументов")
        return STATUS_ERROR
    session.running = False
    return STATUS_OK


COMMANDS = {
    "ls": fs_commands.cmd_ls,
    "cd": fs_commands.cmd_cd,
    "du": fs_commands.cmd_du,
    "find": fs_commands.cmd_find,
    "chmod": chmod_command.cmd_chmod,
    "vfs-info": cmd_vfs_info,
    "exit": cmd_exit,
}
