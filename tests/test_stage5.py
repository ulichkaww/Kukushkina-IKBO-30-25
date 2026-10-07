"""Тесты этапа 5: chmod."""

import os
import unittest

import helpers
import chmod_command
import emulator
import vfs
from session import STATUS_ERROR, STATUS_OK, Session

DEMO = os.path.join(helpers.ROOT, "vfs", "demo.xml")


def make_session():
    """Создать сеанс с VFS demo."""
    return Session(*vfs.load_vfs(DEMO))


def run(session, line):
    """Выполнить команду, вернуть (статус, строки вывода)."""
    status, out = helpers.capture(emulator.execute, session, line)
    return status, out.splitlines()


def mode_of(session, path):
    """Права узла по пути в виде строки rwx."""
    return vfs.mode_string(vfs.lookup(session.root, vfs.resolve([], path)))


class ModeParsingTest(unittest.TestCase):
    """Вычисление новых прав."""

    def test_octal(self):
        """Восьмеричная запись."""
        self.assertEqual(chmod_command.new_mode("640", 0o777), 0o640)
        self.assertEqual(chmod_command.new_mode("0755", 0), 0o755)
        self.assertEqual(chmod_command.new_mode("7", 0o777), 0o007)

    def test_symbolic(self):
        """Символьная запись: +, -, =, u/g/o/a, список."""
        new_mode = chmod_command.new_mode
        self.assertEqual(new_mode("u+x", 0o644), 0o744)
        self.assertEqual(new_mode("go-r", 0o644), 0o600)
        self.assertEqual(new_mode("a=r", 0o755), 0o444)
        self.assertEqual(new_mode("+x", 0o644), 0o755)
        self.assertEqual(new_mode("g=rw,o=", 0o777), 0o760)
        self.assertEqual(new_mode("u=rwx,go=rx", 0), 0o755)

    def test_invalid(self):
        """Неверные записи режима."""
        for spec in ("u+z", "888", "x", "a+x,", "u~x", "u+x;"):
            with self.assertRaises(chmod_command.ModeError, msg=spec):
                chmod_command.new_mode(spec, 0o644)


class ChmodCommandTest(unittest.TestCase):
    """Команда chmod на VFS."""

    def test_octal_and_ls(self):
        """chmod меняет права, ls -l показывает результат."""
        session = make_session()
        self.assertEqual(run(session, "chmod 600 readme.txt")[0], STATUS_OK)
        self.assertEqual(mode_of(session, "readme.txt"), "-rw-------")
        self.assertIn("-rw-------     52 readme.txt",
                      run(session, "ls -l")[1])

    def test_several_paths_and_relative(self):
        """Несколько путей, относительные пути."""
        session = make_session()
        run(session, "cd home/alex")
        run(session, "chmod u+x,g=r notes.txt docs/plan.txt")
        self.assertEqual(mode_of(session, "home/alex/notes.txt"),
                         "-rwxr--r--")
        self.assertEqual(mode_of(session, "home/alex/docs/plan.txt"),
                         "-rwxr--r--")

    def test_recursive(self):
        """-R меняет права всего поддерева."""
        session = make_session()
        run(session, "chmod -R go-rwx home")
        for path in ("home", "home/alex", "home/alex/docs",
                     "home/alex/docs/plan.txt"):
            self.assertTrue(mode_of(session, path).endswith("------"), path)
        self.assertEqual(mode_of(session, "readme.txt"), "-rw-r--r--")

    def test_without_r_only_target(self):
        """Без -R потомки не меняются."""
        session = make_session()
        run(session, "chmod 700 home")
        self.assertEqual(mode_of(session, "home/alex"), "drwxr-xr-x")

    def test_affects_other_commands(self):
        """Права влияют на cd и ls."""
        session = make_session()
        run(session, "chmod 000 secret")
        self.assertEqual(run(session, "cd secret")[0], STATUS_ERROR)
        self.assertEqual(run(session, "ls secret")[0], STATUS_ERROR)
        run(session, "chmod 700 secret")
        self.assertEqual(run(session, "cd secret")[0], STATUS_OK)

    def test_only_memory(self):
        """Файл VFS на диске не меняется."""
        with open(DEMO, "rb") as file:
            before = file.read()
        run(make_session(), "chmod -R 000 /")
        with open(DEMO, "rb") as file:
            self.assertEqual(file.read(), before)

    def test_errors(self):
        """Ошибки: нет операндов, неверный режим, нет пути."""
        session = make_session()
        cases = ("chmod", "chmod 644", "chmod 999 readme.txt",
                 "chmod u+q readme.txt", "chmod 644 nofile",
                 "chmod -R", "chmod -R 644")
        for line in cases:
            status, lines = run(session, line)
            self.assertEqual(status, STATUS_ERROR, line)
            self.assertTrue(lines[0].startswith("chmod:"), line)
        self.assertEqual(mode_of(session, "readme.txt"), "-rw-r--r--")

    def test_partial_error_keeps_going(self):
        """Ошибка в одном пути не мешает остальным."""
        session = make_session()
        status, _ = run(session, "chmod 600 nofile readme.txt")
        self.assertEqual(status, STATUS_ERROR)
        self.assertEqual(mode_of(session, "readme.txt"), "-rw-------")


if __name__ == "__main__":
    unittest.main()
