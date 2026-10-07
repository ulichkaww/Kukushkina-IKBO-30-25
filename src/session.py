"""Состояние сеанса эмулятора."""

import vfs

STATUS_OK = 0
STATUS_ERROR = 1
DEFAULT_VFS_NAME = "vfs"


class Session:
    """Хранит VFS в памяти, текущую папку и признак продолжения работы."""

    def __init__(self, vfs_name=DEFAULT_VFS_NAME, root=None):
        """Создать сеанс: имя VFS и корневой каталог в памяти."""
        self.vfs_name = vfs_name
        self.root = root if root is not None else vfs.empty_vfs()
        self.cwd = []
        self.running = True

    def cwd_path(self):
        """Абсолютный путь текущей папки внутри VFS."""
        return vfs.join_path(self.cwd)

    def prompt(self):
        """Вернуть приглашение: имя VFS и текущая папка."""
        return f"{self.vfs_name}:{self.cwd_path()}$ "
