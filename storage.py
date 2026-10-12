"""JSON 持久化与 CSV 导出；错误交给调用者决定如何显示。"""

import csv
import json
import os
import tempfile
from dataclasses import dataclass, field
'''程序运行时创建用完可以自动删掉的文件,退出自动清理'''
from pathlib import Path
'''Python 标准库，把内置工具包引进当前代码'''

from core import validate_library
from migration import migrate_library


class LibraryDataError(ValueError):
    """JSON 语法或音乐库数据不合法。"""


@dataclass
class LibraryLoadResult:
    songs: list[dict]
    migrated_count: int = 0
    skipped: list[dict] = field(default_factory=list)
    error_report: Path | None = None


def _write_import_report(path: Path, skipped: list[dict]) -> Path:
    report = {"skipped": skipped}
    base = path.parent / "songs_import_errors.json"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{base.name}.", suffix=".tmp", delete=False,
        ) as file:
            temp_path = Path(file.name)
            json.dump(report, file, ensure_ascii=False, indent=2)
            file.write("\n")
        suffix = 0
        while True:
            candidate = base if suffix == 0 else base.with_name(
                f"{base.stem}_{suffix}{base.suffix}"
            )
            try:
                # Hard-link creation publishes the complete file without ever
                # replacing a report created by an earlier import.
                if os.name == "nt":
                    # Windows rename fails rather than replacing an existing path.
                    os.rename(temp_path, candidate)
                    temp_path = None
                else:
                    os.link(temp_path, candidate)
                return candidate
            except FileExistsError:
                suffix += 1
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def load_library(filename: str | Path) -> LibraryLoadResult:
    path = Path(filename)
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return LibraryLoadResult([])
    except (json.JSONDecodeError, UnicodeError) as error:
        raise LibraryDataError(f"无法解析数据文件：{error}") from error
    try:
        result = migrate_library(data)
        validate_library(result.songs)
    except ValueError as error:
        raise LibraryDataError(f"数据文件内容不合法：{error}") from error
    report_path = None
    if result.skipped:
        try:
            report_path = _write_import_report(path, result.skipped)
        except OSError as error:
            raise LibraryDataError(f"无法写入导入错误报告，原音乐库未更改：{error}") from error
    if result.migrated_count or result.skipped:
        try:
            save_library(result.songs, path)
        except (OSError, ValueError) as error:
            raise LibraryDataError(f"无法保存迁移后的音乐库：{error}") from error
    return LibraryLoadResult(result.songs, result.migrated_count, result.skipped, report_path)


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
