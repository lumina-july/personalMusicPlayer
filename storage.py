"""JSON 持久化与 CSV 导出；错误交给调用者决定如何显示。"""

import csv
import json
import os
import tempfile
'''程序运行时创建用完可以自动删掉的文件,退出自动清理'''
from pathlib import Path
'''Python 标准库，把内置工具包引进当前代码'''

from core import validate_library


class LibraryDataError(ValueError):
    """JSON 语法或音乐库数据不合法。"""


def load_library(filename: str | Path) -> list[dict]:
    path = Path(filename)
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, UnicodeError) as error:
        raise LibraryDataError(f"无法解析数据文件：{error}") from error
    try:
        validate_library(data)
    except ValueError as error:
        raise LibraryDataError(f"数据文件内容不合法：{error}") from error
    return data


def save_library(library: list[dict], filename: str | Path) -> None:
    """先写同目录临时文件，再替换目标文件，降低截断原文件的风险。"""
    validate_library(library)
    path = Path(filename)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as file:
            temp_path = Path(file.name)
            json.dump(library, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def export_csv(library: list[dict], filename: str | Path) -> None:
    validate_library(library)
    fields = (
        "id", "title", "artist", "album", "genre",
        "rating", "favorite", "play_count", "comments",
    )
    with Path(filename).open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for song in library:
            row = song.copy()
            row["comments"] = " | ".join(
                comment["text"] for comment in song["comments"]
            )
            writer.writerow(row)
