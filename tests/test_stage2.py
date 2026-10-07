"""Тесты этапа 2: конфигурация и стартовый скрипт."""

import json
import os
import tempfile
import unittest

import helpers
import config
import emulator
from session import STATUS_ERROR, STATUS_OK, Session
import script


def make_args(vfs=None, script_path=None, config_path=None):
    """Собрать разобранные параметры вручную."""
    parser = config.build_arg_parser()
    argv = []
    for name, value in (("--vfs", vfs), ("--script", script_path),
                        ("--config", config_path)):
        if value is not None:
            argv += [name, value]
    return parser.parse_args(argv)


class ConfigTest(unittest.TestCase):
    """Проверка чтения параметров."""

    def write_json(self, text):
        """Создать временный файл с текстом и вернуть путь."""
        handle, path = tempfile.mkstemp(suffix=".json")
        self.addCleanup(os.remove, path)
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write(text)
        return path

    def test_file_values(self):
        """Значения берутся из файла."""
        path = self.write_json(json.dumps({"vfs": "a", "script": "b"}))
        settings = config.load_settings(make_args(config_path=path))
        self.assertEqual((settings.vfs, settings.script), ("a", "b"))
        self.assertEqual(settings.sources["vfs"], config.SOURCE_FILE)

    def test_cli_has_priority(self):
        """Командная строка важнее файла."""
        path = self.write_json(json.dumps({"vfs": "a", "script": "b"}))
        args = make_args(vfs="cli", config_path=path)
        settings = config.load_settings(args)
        self.assertEqual((settings.vfs, settings.script), ("cli", "b"))
        self.assertEqual(settings.sources["vfs"], config.SOURCE_CLI)

    def test_errors(self):
        """Ошибки чтения конфигурации."""
        bad_inputs = ["{", "[]", '{"vfs": 1}', '{"other": "x"}']
        for text in bad_inputs:
            args = make_args(config_path=self.write_json(text))
            with self.assertRaises(config.ConfigError):
                config.load_settings(args)
        with self.assertRaises(config.ConfigError):
            config.load_settings(make_args(config_path="/no/such.json"))

    def test_describe_lists_all_params(self):
        """Отладочный вывод содержит все параметры."""
        text = "\n".join(config.describe(config.load_settings(make_args())))
        for key in ("vfs", "script", "config"):
            self.assertIn(key, text)


class ScriptTest(unittest.TestCase):
    """Проверка стартового скрипта."""

    def write_script(self, text):
        """Создать временный скрипт."""
        handle, path = tempfile.mkstemp(suffix=".txt")
        self.addCleanup(os.remove, path)
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write(text)
        return path

    def test_shows_input_and_output(self):
        """В диалоге видны и ввод, и вывод."""
        path = self.write_script("# c\nvfs-info\n")
        status, out = helpers.capture(
            script.run_script, Session(), path, emulator.execute)
        self.assertEqual(status, STATUS_OK)
        self.assertEqual(
            out, "vfs:/$ vfs-info\nVFS 'vfs': 0 каталогов, 0 файлов\n")

    def test_stops_on_first_error(self):
        """После первой ошибки остальные строки не выполняются."""
        path = self.write_script("cd a b\nls never\n")
        status, out = helpers.capture(
            script.run_script, Session(), path, emulator.execute)
        self.assertEqual(status, STATUS_ERROR)
        self.assertNotIn("never", out.replace("ls never", ""))
        self.assertIn("строка 1", out)

    def test_missing_script(self):
        """Отсутствующий скрипт — ScriptReadError."""
        with self.assertRaises(script.ScriptReadError):
            script.read_script("/no/such/script.txt")

    def test_main_reports_config_error(self):
        """main возвращает код ошибки при плохом конфиге."""
        status, out = helpers.capture(
            emulator.main, ["--config", "/no/such.json"])
        self.assertEqual(status, emulator.EXIT_CONFIG_ERROR)
        self.assertIn("Ошибка конфигурации", out)


if __name__ == "__main__":
    unittest.main()
