"""Тесты этапа 4: ls, cd, du, find."""

import os
import unittest

import helpers
import emulator
import fs_commands
import vfs
from session import STATUS_ERROR, STATUS_OK, Session


def make_session(name="demo.xml"):
    """Создать сеанс с VFS из папки vfs проекта."""
    path = os.path.join(helpers.ROOT, "vfs", name)
    return Session(*vfs.load_vfs(path))


def run(session, line):
    """Выполнить команду, вернуть (статус, строки вывода)."""
    status, out = helpers.capture(emulator.execute, session, line)
    return status, out.splitlines()


class LsTest(unittest.TestCase):
    """Команда ls."""

    def test_root(self):
        """Содержимое корня."""
        self.assertEqual(run(make_session(), "ls"),
                         (STATUS_OK, ["bin", "home", "readme.txt", "secret"]))

    def test_hidden_files(self):
        """Скрытые файлы видны только с -a."""
        session = make_session()
        self.assertNotIn(".hidden", run(session, "ls home/alex")[1])
        self.assertIn(".hidden", run(session, "ls -a home/alex")[1])

    def test_long_format(self):
        """Формат -l: права, размер, имя."""
        lines = run(make_session(), "ls -l")[1]
        self.assertIn("-rw-r--r--     52 readme.txt", lines)
        self.assertIn("drwxr-xr-x      0 bin", lines)

    def test_file_and_many_operands(self):
        """Файл и несколько операндов, заголовки каталогов."""
        status, lines = run(make_session(), "ls readme.txt bin home")
        self.assertEqual(status, STATUS_OK)
        self.assertEqual(lines, ["readme.txt", "", "bin:", "tool", "",
                                 "home:", "alex", "guest"])

    def test_errors(self):
        """Нет пути, неверная опция."""
        session = make_session()
        status, lines = run(session, "ls nofile")
        self.assertEqual(status, STATUS_ERROR)
        self.assertIn("Нет такого файла", lines[0])
        self.assertEqual(run(session, "ls -z")[0], STATUS_ERROR)

    def test_permission_denied(self):
        """Каталог без права чтения."""
        status, lines = run(make_session("locked.xml"), "ls private")
        self.assertEqual(status, STATUS_ERROR)
        self.assertIn("Отказано в доступе", lines[0])


class CdTest(unittest.TestCase):
    """Команда cd."""

    def test_navigation(self):
        """Относительные, абсолютные пути, '..' и возврат в корень."""
        session = make_session()
        run(session, "cd home/alex")
        self.assertEqual(session.cwd_path(), "/home/alex")
        run(session, "cd ../guest")
        self.assertEqual(session.cwd_path(), "/home/guest")
        run(session, "cd /home/alex/docs")
        self.assertEqual(session.cwd_path(), "/home/alex/docs")
        run(session, "cd ../../..")
        self.assertEqual(session.cwd_path(), "/")
        run(session, "cd ../..")
        self.assertEqual(session.cwd_path(), "/")
        run(session, "cd home")
        run(session, "cd")
        self.assertEqual(session.cwd_path(), "/")

    def test_prompt_follows_cwd(self):
        """Приглашение содержит имя VFS и текущую папку."""
        session = make_session()
        run(session, "cd home")
        self.assertEqual(session.prompt(), "demo:/home$ ")

    def test_errors(self):
        """Нет каталога, файл вместо каталога, лишние аргументы."""
        session = make_session()
        for line in ("cd nofile", "cd readme.txt", "cd a b"):
            self.assertEqual(run(session, line)[0], STATUS_ERROR, line)
        self.assertEqual(session.cwd_path(), "/")

    def test_no_exec_permission(self):
        """Каталог без права входа."""
        session = make_session("locked.xml")
        self.assertEqual(run(session, "cd noexec")[0], STATUS_ERROR)
        self.assertEqual(run(session, "cd private")[0], STATUS_ERROR)
        self.assertEqual(run(session, "ls noexec")[1], ["y.txt"])


class DuTest(unittest.TestCase):
    """Команда du."""

    def test_directory_tree(self):
        """Размеры каталогов считаются рекурсивно."""
        status, lines = run(make_session(), "du home")
        self.assertEqual(status, STATUS_OK)
        self.assertEqual(lines[-1], "97\thome")
        self.assertIn("48\thome/alex/docs", lines)

    def test_summary_all_and_human(self):
        """Опции -s, -a, -h."""
        session = make_session()
        self.assertEqual(run(session, "du -s home")[1], ["97\thome"])
        self.assertEqual(len(run(session, "du -a home/alex")[1]), 7)
        self.assertEqual(run(session, "du -h readme.txt")[1],
                         ["52B\treadme.txt"])

    def test_human_size(self):
        """Единицы измерения."""
        self.assertEqual(fs_commands.human_size(512), "512B")
        self.assertEqual(fs_commands.human_size(1536), "1.5K")
        self.assertEqual(fs_commands.human_size(3 * 1024 * 1024), "3.0M")

    def test_errors(self):
        """Нет пути, неверная опция, закрытый каталог."""
        session = make_session("locked.xml")
        self.assertEqual(run(session, "du nofile")[0], STATUS_ERROR)
        self.assertEqual(run(session, "du -x")[0], STATUS_ERROR)
        status, lines = run(session, "du private")
        self.assertEqual(status, STATUS_ERROR)
        self.assertEqual(lines[0], "0\tprivate")


class FindTest(unittest.TestCase):
    """Команда find."""

    def test_name(self):
        """Поиск по шаблону имени."""
        status, lines = run(make_session(), "find home -name *.txt")
        self.assertEqual(status, STATUS_OK)
        self.assertEqual(lines, ["home/alex/docs/plan.txt",
                                 "home/alex/notes.txt",
                                 "home/guest/hello.txt"])

    def test_type(self):
        """Поиск по типу."""
        session = make_session()
        dirs = run(session, "find / -type d")[1]
        self.assertEqual(dirs[0], "/")
        self.assertIn("/home/alex/docs", dirs)
        files = run(session, "find home/alex -type f -name *.md")[1]
        self.assertEqual(files, ["home/alex/docs/report.md"])

    def test_default_path_and_relative(self):
        """Путь по умолчанию — текущая папка."""
        session = make_session()
        run(session, "cd home/guest")
        self.assertEqual(run(session, "find")[1], [".", "./hello.txt"])

    def test_errors(self):
        """Нет пути, неверные предикаты, закрытый каталог."""
        session = make_session("locked.xml")
        for line in ("find nofile", "find -name", "find -type x",
                     "find -foo bar", "find private"):
            self.assertEqual(run(session, line)[0], STATUS_ERROR, line)


if __name__ == "__main__":
    unittest.main()
