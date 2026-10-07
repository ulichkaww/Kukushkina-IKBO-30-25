"""Виртуальная файловая система: модель в памяти и загрузка из XML.

Формат XML::

    <vfs name="demo">
      <dir name="home" mode="755">
        <file name="a.txt" mode="644">текст</file>
        <file name="b.bin" encoding="base64">AAEC/w==</file>
      </dir>
    </vfs>
"""

import base64
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

DEFAULT_DIR_MODE = 0o755
DEFAULT_FILE_MODE = 0o644
MODE_PATTERN = re.compile(r"[0-7]{3,4}")
OCTAL_BASE = 8
BASE64 = "base64"
TEXT_ENCODING = "utf-8"
FORBIDDEN_NAMES = ("", ".", "..")
OWNER_READ = 0o400
OWNER_EXEC = 0o100
PERMISSION_BITS = "rwxrwxrwx"


class VfsError(Exception):
    """Ошибка загрузки VFS."""


@dataclass
class Node:
    """Общие поля узла: имя и права доступа."""

    name: str
    mode: int


@dataclass
class File(Node):
    """Файл: содержимое хранится в байтах."""

    data: bytes = b""

    @property
    def size(self):
        """Размер файла в байтах."""
        return len(self.data)


@dataclass
class Dir(Node):
    """Каталог: словарь имя -> узел."""

    children: dict = field(default_factory=dict)


def parse_mode(element, default):
    """Прочитать атрибут mode (восьмеричный) или взять значение по умолчанию."""
    text = element.get("mode")
    if text is None:
        return default
    if not MODE_PATTERN.fullmatch(text):
        raise VfsError(f"неверные права '{text}' у <{element.tag}>")
    return int(text, OCTAL_BASE)


def parse_name(element):
    """Прочитать и проверить атрибут name."""
    name = element.get("name")
    if name is None:
        raise VfsError(f"у <{element.tag}> нет атрибута name")
    if name in FORBIDDEN_NAMES or "/" in name or "\0" in name:
        raise VfsError(f"недопустимое имя '{name}'")
    return name


def decode_content(element, name):
    """Получить байты файла (текст или base64)."""
    text = element.text or ""
    encoding = element.get("encoding")
    if encoding is None:
        return text.encode(TEXT_ENCODING)
    if encoding != BASE64:
        raise VfsError(f"файл '{name}': неизвестная кодировка '{encoding}'")
    try:
        return base64.b64decode("".join(text.split()), validate=True)
    except ValueError as err:
        raise VfsError(f"файл '{name}': неверный base64") from err


def build_file(element):
    """Создать File из элемента <file>."""
    name = parse_name(element)
    if len(element):
        raise VfsError(f"файл '{name}' не может содержать вложенные элементы")
    mode = parse_mode(element, DEFAULT_FILE_MODE)
    return File(name, mode, decode_content(element, name))


def build_children(element, directory):
    """Заполнить каталог дочерними узлами."""
    for child in element:
        node = build_node(child)
        if node.name in directory.children:
            raise VfsError(f"повторяющееся имя '{node.name}'")
        directory.children[node.name] = node


def build_dir(element, name):
    """Создать Dir из элемента <dir> или корневого <vfs>."""
    directory = Dir(name, parse_mode(element, DEFAULT_DIR_MODE))
    build_children(element, directory)
    return directory


def build_node(element):
    """Создать узел по тегу элемента."""
    if element.tag == "file":
        return build_file(element)
    if element.tag == "dir":
        return build_dir(element, parse_name(element))
    raise VfsError(f"неизвестный элемент <{element.tag}>")


def load_vfs(path):
    """Загрузить VFS из XML-файла в память.

    Возвращает пару (имя VFS, корневой Dir). Файлы на диске не меняются.
    """
    try:
        tree = ET.parse(path)
    except FileNotFoundError as err:
        raise VfsError(f"файл не найден: {path}") from err
    except ET.ParseError as err:
        raise VfsError(f"неверный формат XML в {path}: {err}") from err
    except OSError as err:
        raise VfsError(f"не удалось прочитать {path}: {err}") from err
    root_element = tree.getroot()
    if root_element.tag != "vfs":
        raise VfsError("корневой элемент должен называться <vfs>")
    stem = os.path.splitext(os.path.basename(path))[0]
    name = root_element.get("name") or stem
    return name, build_dir(root_element, "")


def empty_vfs():
    """Создать пустую корневую папку."""
    return Dir("", DEFAULT_DIR_MODE)


def walk(directory, depth=0):
    """Обойти дерево: выдаёт (глубина, узел) в алфавитном порядке."""
    for name in sorted(directory.children):
        node = directory.children[name]
        yield depth, node
        if isinstance(node, Dir):
            yield from walk(node, depth + 1)


def resolve(cwd, path):
    """Построить список имён пути; cwd — список имён текущей папки.

    Поддерживаются абсолютные и относительные пути, '.' и '..'.
    """
    parts = [] if path.startswith("/") else list(cwd)
    for piece in path.split("/"):
        if piece in ("", "."):
            continue
        if piece == "..":
            if parts:
                parts.pop()
        else:
            parts.append(piece)
    return parts


def lookup(root, parts):
    """Найти узел по списку имён; None, если пути нет."""
    node = root
    for name in parts:
        if not isinstance(node, Dir) or name not in node.children:
            return None
        node = node.children[name]
    return node


def join_path(parts):
    """Собрать абсолютный путь из списка имён."""
    return "/" + "/".join(parts)


def child_label(prefix, name):
    """Путь к потомку в том виде, как пользователь указал начало."""
    if prefix.endswith("/"):
        return prefix + name
    return prefix + "/" + name


def can_read(node):
    """Есть ли у владельца право чтения."""
    return bool(node.mode & OWNER_READ)


def can_enter(node):
    """Есть ли у владельца право входа (x)."""
    return bool(node.mode & OWNER_EXEC)


def entry_size(node):
    """Размер записи: размер файла или 0 для каталога."""
    return node.size if isinstance(node, File) else 0


def mode_string(node):
    """Права в виде строки, например drwxr-xr-x."""
    kind = "d" if isinstance(node, Dir) else "-"
    bits = "".join(
        letter if node.mode & (1 << (len(PERMISSION_BITS) - 1 - index))
        else "-"
        for index, letter in enumerate(PERMISSION_BITS))
    return kind + bits
