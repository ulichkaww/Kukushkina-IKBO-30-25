"""Тесты этапа 1: парсер, ошибки, exit (ls и cd позже стали настоящими)."""

import os
import unittest

import helpers
import cmdline
import emulator
from session import STATUS_ERROR, STATUS_OK, Session


class ParserTest(unittest.TestCase):
    """Проверка разбора строки."""

    def test_env_expansion(self):
        """$VAR и ${VAR} раскрываются."""
        os.environ["EMU_TEST"] = "value"
        self.assertEqual(cmdline.parse_line("ls $EMU_TEST"), ["ls", "value"])
        self.assertEqual(cmdline.parse_line("ls ${EMU_TEST}x"),
                         ["ls", "valuex"])

    def test_unknown_variable_is_empty(self):
        """Неизвестная переменная даёт пустую строку."""
        os.environ.pop("EMU_NOPE", None)
        self.assertEqual(cmdline.parse_line("ls a$EMU_NOPE"), ["ls", "a"])

    def test_quotes(self):
        """Кавычки объединяют слова в один аргумент."""
        self.assertEqual(cmdline.parse_line('ls "a b"'), ["ls", "a b"])

    def test_unclosed_quote(self):
        """Незакрытая кавычка — ошибка разбора."""
        with self.assertRaises(cmdline.ParseError):
            cmdline.parse_line('ls "a')


def run_line(session, line):
    """Выполнить строку, вернуть (статус, вывод)."""
    return helpers.capture(emulator.execute, session, line)


class CommandTest(unittest.TestCase):
    """Проверка диспетчера команд и ошибок."""

    def test_ls_and_cd_are_known(self):
        """ls и cd распознаются как команды."""
        session = Session()
        self.assertEqual(run_line(session, "ls"), (STATUS_OK, ""))
        self.assertEqual(run_line(session, "cd /"), (STATUS_OK, ""))

    def test_unknown_command(self):
        """Неизвестная команда сообщает об ошибке."""
        status, out = run_line(Session(), "foo")
        self.assertEqual(status, STATUS_ERROR)
        self.assertIn("команда не найдена", out)

    def test_bad_arguments(self):
        """Неверные аргументы cd и exit — ошибка."""
        session = Session()
        self.assertEqual(run_line(session, "cd a b")[0], STATUS_ERROR)
        self.assertEqual(run_line(session, "exit 1")[0], STATUS_ERROR)
        self.assertTrue(session.running)

    def test_exit(self):
        """exit останавливает сеанс."""
        session = Session()
        run_line(session, "exit")
        self.assertFalse(session.running)

    def test_prompt_has_vfs_name(self):
        """Приглашение содержит имя VFS."""
        self.assertIn("demo", Session("demo").prompt())


if __name__ == "__main__":
    unittest.main()
