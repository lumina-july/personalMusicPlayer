"""针对 core.filter_songs(..., "commented") 的 pytest 示例。

从本文件所在目录运行："""

import core


def test_returns_only_songs_with_comments():
    library = [
        {"id": 1, "comments": [{"id": 1, "text": "很好听的一首歌"}]},
        {"id": 2, "comments": []},
        {"id": 3, "comments": [{"id": 1, "text": "值得再听一次"}]},
    ]

    results = core.filter_songs(library, "commented")

    assert [song["id"] for song in results] == [1, 3]


def test_empty_library_returns_empty_results():
    results = core.filter_songs([], "commented")

    assert results == []
