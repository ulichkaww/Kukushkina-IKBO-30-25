"""Тесты этапа 3: загрузка VFS из XML."""

import os
import unittest

import helpers
import emulator
import vfs
from session import Session

VFS_DIR = os.path.join(helpers.ROOT, "vfs")


def load(name):
    """Загрузить VFS из папки vfs проекта."""
    return vfs.load_vfs(os.path.join(VFS_DIR, name))


class LoadTest(unittest.TestCase):
    """Успешная загрузка разных вариантов VFS."""

    def test_minimal(self):
        """Минимальная VFS: один файл."""
        name, root = load("minimal.xml")
        self.assertEqual(name, "minimal")
        self.assertEqual(root.children["readme.txt"].data, b"minimal vfs")

    def test_several_files_and_base64(self):
        """Несколько файлов; двоичные данные из base64."""
        _, root = load("files.xml")
        self.assertEqual(len(root.children), 4)
        self.assertEqual(root.children["data.bin"].data, bytes(range(16)))
        self.assertEqual(root.children["notes.txt"].mode, 0o600)

    def test_three_levels(self):
        """Не менее трёх уровней вложенности."""
        _, root = load("deep.xml")
        node = root
        for part in ("level1", "level2", "level3", "level4"):
            node = node.children[part]
        self.assertEqual(node.children["four.txt"].data, b"4444")

    def test_default_modes(self):
        """Права по умолчанию: 755 для каталога, 644 для файла."""
        _, root = load("deep.xml")
        self.assertEqual(root.children["empty"].mode, vfs.DEFAULT_DIR_MODE)
        file_node = root.children["level1"].children["one.txt"]
        self.assertEqual(file_node.mode, vfs.DEFAULT_FILE_MODE)


class ErrorTest(unittest.TestCase):
    """Ошибки загрузки VFS."""

    def test_invalid_files(self):
        """Каждый неверный файл даёт VfsError."""
        folder = os.path.join(VFS_DIR, "invalid")
        names = sorted(os.listdir(folder))
        self.assertGreaterEqual(len(names), 5)
        for name in names:
            with self.assertRaises(vfs.VfsError, msg=name):
                vfs.load_vfs(os.path.join(folder, name))

    def test_not_found(self):
        """Отсутствующий файл."""
        with self.assertRaises(vfs.VfsError):
            vfs.load_vfs("/no/such/vfs.xml")

    def test_main_reports_error(self):
        """main сообщает об ошибке загрузки и возвращает код 2."""
        status, out = helpers.capture(
            emulator.main, ["--vfs", "/no/such/vfs.xml"])
        self.assertEqual(status, emulator.EXIT_CONFIG_ERROR)
        self.assertIn("Ошибка загрузки VFS", out)


class InfoTest(unittest.TestCase):
    """Служебная команда vfs-info."""

    def test_info(self):
        """vfs-info показывает сводку и дерево."""
        name, root = load("deep.xml")
        _, out = helpers.capture(
            emulator.execute, Session(name, root), "vfs-info")
        self.assertIn("5 каталогов, 4 файлов", out)
        self.assertIn("four.txt", out)


if __name__ == "__main__":
    unittest.main()
