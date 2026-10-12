import json

import pytest

import core
import storage


def old_song(**kwargs):
    return {"title": "Track", "artist": "Singer", **kwargs}


def test_migrates_missing_fields_and_assigns_ids_after_source_max(tmp_path):
    path = tmp_path / "songs.json"
    path.write_text(json.dumps([
        old_song(id=4),
        {"title": "Second", "artist": "Singer", "id": 8, "album": "A"},
        {"title": "Third", "artist": "Singer"},
    ]), encoding="utf-8")

    result = storage.load_library(path)

    assert result.migrated_count == 3
    assert [song["id"] for song in result.songs] == [4, 8, 9]
    assert result.songs[0] == {
        "title": "Track", "artist": "Singer", "id": 4, "album": "", "genre": "",
        "rating": None, "favorite": False, "play_count": 0, "comments": [],
    }
    assert json.loads(path.read_text(encoding="utf-8")) == result.songs
    assert result.error_report is None


def test_generates_distinct_title_numbers_avoiding_existing_titles():
    from migration import migrate_library

    records = [
        {"title": "Singer 未知1", "artist": "Singer", "id": 1},
        {"artist": "Singer", "id": 2},
        {"artist": "Singer", "id": 3},
    ]
    result = migrate_library(records)
    assert [song["title"] for song in result.songs] == [
        "Singer 未知1", "Singer 未知2", "Singer 未知3",
    ]
    assert core.TITLE_MAX == 120
    assert len(result.songs[-1]["title"]) <= core.TITLE_MAX


def test_missing_artist_is_filled_and_missing_both_is_reported(tmp_path):
    path = tmp_path / "songs.json"
    path.write_text(json.dumps([
        {"title": "Solo", "id": 1},
        {"id": 2},
        {"title": "Good", "artist": "Artist", "id": 3},
    ]), encoding="utf-8")
    result = storage.load_library(path)
    assert [(song["title"], song["artist"]) for song in result.songs] == [
        ("Solo", "未知歌手"), ("Good", "Artist")
    ]
    report = json.loads(result.error_report.read_text(encoding="utf-8"))
    assert report["skipped"][0]["record"] == {"id": 2}
    assert "同时缺少" in report["skipped"][0]["reason"]


def test_invalid_fields_and_duplicate_ids_are_skipped(tmp_path):
    path = tmp_path / "songs.json"
    path.write_text(json.dumps([
        old_song(id=1), old_song(id=1), old_song(id=3, favorite="yes"),
        old_song(id=4, play_count=-1), old_song(id=5),
    ]), encoding="utf-8")
    result = storage.load_library(path)
    assert [song["id"] for song in result.songs] == [1, 5]
    report = json.loads(result.error_report.read_text(encoding="utf-8"))
    assert len(report["skipped"]) == 3
    assert "重复歌曲 id" in report["skipped"][0]["reason"]
    assert "favorite" in report["skipped"][1]["reason"]
    assert "play_count" in report["skipped"][2]["reason"]


def test_existing_report_is_not_overwritten(tmp_path):
    path = tmp_path / "songs.json"
    path.write_text(json.dumps([{"id": 1}]), encoding="utf-8")
    old_report = tmp_path / "songs_import_errors.json"
    old_report.write_text("keep", encoding="utf-8")
    result = storage.load_library(path)
    assert old_report.read_text(encoding="utf-8") == "keep"
    assert result.error_report.name == "songs_import_errors_1.json"


def test_report_failure_preserves_original_library(tmp_path, monkeypatch):
    path = tmp_path / "songs.json"
    original = json.dumps([{"id": 1}], ensure_ascii=False)
    path.write_text(original, encoding="utf-8")

    def fail(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(storage, "_write_import_report", fail)
    with pytest.raises(storage.LibraryDataError, match="原音乐库未更改"):
        storage.load_library(path)
    assert path.read_text(encoding="utf-8") == original


def test_malformed_json_is_not_rewritten(tmp_path):
    path = tmp_path / "songs.json"
    original = "[{bad json"
    path.write_text(original, encoding="utf-8")
    with pytest.raises(storage.LibraryDataError, match="无法解析"):
        storage.load_library(path)
    assert path.read_text(encoding="utf-8") == original


def test_current_library_is_not_rewritten(tmp_path):
    path = tmp_path / "songs.json"
    data = [{"id": 1, "title": "T", "artist": "A", "album": "", "genre": "",
             "rating": None, "favorite": False, "play_count": 0, "comments": []}]
    original = json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(original, encoding="utf-8")
    result = storage.load_library(path)
    assert result.migrated_count == 0
    assert path.read_text(encoding="utf-8") == original
