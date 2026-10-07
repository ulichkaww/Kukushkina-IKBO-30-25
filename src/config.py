"""Параметры запуска: командная строка и конфигурационный файл JSON."""

import argparse
import json
from dataclasses import dataclass, field

CONFIG_KEYS = ("vfs", "script")
SOURCE_CLI = "командная строка"
SOURCE_FILE = "конфигурационный файл"
SOURCE_NONE = "не задан"


class ConfigError(Exception):
    """Ошибка чтения или проверки конфигурации."""


@dataclass
class Settings:
    """Итоговые параметры: значение и источник каждого."""

    values: dict = field(default_factory=dict)
    sources: dict = field(default_factory=dict)

    @property
    def vfs(self):
        """Путь к физическому расположению VFS."""
        return self.values.get("vfs")

    @property
    def script(self):
        """Путь к стартовому скрипту."""
        return self.values.get("script")


def build_arg_parser():
    """Создать разбор параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog="emulator",
        description="Эмулятор командной строки UNIX-подобной ОС")
    parser.add_argument("--vfs", help="путь к физическому расположению VFS")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    parser.add_argument("--config", help="путь к конфигурационному файлу")
    return parser


def read_config_file(path):
    """Прочитать JSON-конфигурацию и вернуть словарь параметров."""
    try:
        with open(path, encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as err:
        raise ConfigError(f"файл не найден: {path}") from err
    except (OSError, UnicodeDecodeError) as err:
        raise ConfigError(f"не удалось прочитать {path}: {err}") from err
    except json.JSONDecodeError as err:
        raise ConfigError(f"неверный JSON в {path}: {err}") from err
    return validate_config(data, path)


def validate_config(data, path):
    """Проверить, что конфигурация — объект с известными строковыми полями."""
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: ожидался JSON-объект")
    for key, value in data.items():
        if key not in CONFIG_KEYS:
            raise ConfigError(f"{path}: неизвестный параметр '{key}'")
        if not isinstance(value, str):
            raise ConfigError(f"{path}: параметр '{key}' должен быть строкой")
    return data


def load_settings(args):
    """Объединить параметры: командная строка важнее файла."""
    settings = Settings()
    file_values = read_config_file(args.config) if args.config else {}
    for key in CONFIG_KEYS:
        cli_value = getattr(args, key)
        if cli_value is not None:
            settings.values[key] = cli_value
            settings.sources[key] = SOURCE_CLI
        elif key in file_values:
            settings.values[key] = file_values[key]
            settings.sources[key] = SOURCE_FILE
        else:
            settings.sources[key] = SOURCE_NONE
    settings.values["config"] = args.config
    return settings


def describe(settings):
    """Вернуть строки отладочного вывода всех параметров."""
    lines = ["[параметры запуска]"]
    for key in CONFIG_KEYS:
        value = settings.values.get(key)
        lines.append(f"  {key:<7}= {value} ({settings.sources[key]})")
    lines.append(f"  config = {settings.values['config']}")
    return lines
