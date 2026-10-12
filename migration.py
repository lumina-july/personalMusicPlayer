"""纯数据转换：将旧音乐库记录补全为当前格式，并收集无法导入的记录。"""

from dataclasses import dataclass

import core


@dataclass
class MigrationResult:
    songs: list[dict]
    skipped: list[dict]
    migrated_count: int


def migrate_library(data: list) -> MigrationResult:
    if not isinstance(data, list):
        raise ValueError("JSON 最外层必须是列表")

    # 预先收集源数据中所有有效正整数 ID，避免新 ID 与后续旧记录冲突。
    used_ids = {
        item["id"] for item in data
        if isinstance(item, dict) and core.is_integer(item.get("id")) and item["id"] > 0
    }
    next_id = max(used_ids, default=0) + 1
    # 保留已有标题，以免自动生成标题与后续源记录冲突。
    titles = {
        item["title"] for item in data
        if isinstance(item, dict) and isinstance(item.get("title"), str)
    }
    unknown_numbers: dict[str, int] = {}
    songs, skipped = [], []
    migrated_count = 0
    seen_ids = set()

    for position, original in enumerate(data, start=1):
        def reject(reason):
            skipped.append({"record": original, "reason": f"第 {position} 条记录：{reason}"})

        if not isinstance(original, dict):
            reject("歌曲记录必须是对象")
            continue
        song = original.copy()
        changed = False
        missing_title = "title" not in song
        missing_artist = "artist" not in song
        if missing_title and missing_artist:
            reject("同时缺少 title 和 artist")
            continue

        if missing_artist:
            song["artist"] = "未知歌手"
            changed = True
        if missing_title:
            try:
                artist = core.validate_text(song["artist"], "歌手", 1, core.ARTIST_MAX)
            except ValueError as error:
                reject(f"缺少 title，且 artist 无效：{error}")
                continue
            n = unknown_numbers.get(artist, 0) + 1
            while True:
                suffix = f" 未知{n}"
                title = artist[:core.TITLE_MAX - len(suffix)].rstrip() + suffix
                n += 1
                if title not in titles:
                    break
            unknown_numbers[artist] = n - 1
            song["title"] = title
            titles.add(title)
            changed = True

        if "id" not in song:
            while next_id in used_ids:
                next_id += 1
            song["id"] = next_id
            used_ids.add(next_id)
            next_id += 1
            changed = True

        defaults = {"album": "", "genre": "", "rating": None, "favorite": False,
                    "play_count": 0, "comments": []}
        for field, default in defaults.items():
            if field not in song:
                song[field] = default.copy() if isinstance(default, list) else default
                changed = True

        try:
            core.validate_song(song)
        except ValueError as error:
            reject(str(error))
            continue
        if song["id"] in seen_ids:
            reject(f"重复歌曲 id：{song['id']}")
            continue
        seen_ids.add(song["id"])
        songs.append(song)
        migrated_count += int(changed)

    return MigrationResult(songs, skipped, migrated_count)
