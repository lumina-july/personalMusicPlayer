"""音乐库规则与计算；不读取键盘、不打印、不访问文件。"""

TITLE_MAX = 100
ARTIST_MAX = 100
ALBUM_MAX = 150
GENRE_MAX = 80
COMMENT_MIN = 5
COMMENT_MAX = 1000


def is_integer(value):
    return type(value) is int  # bool 也是 int 的子类，但这里不接受 bool


def validate_text(value, name, minimum=0, maximum=100):
    if not isinstance(value, str):
        raise ValueError(f"{name}必须是文本")
    if not minimum <= len(value.strip()) <= maximum:
        raise ValueError(f"{name}必须是 {minimum}～{maximum} 个字符")
    return value.strip()


def validate_rating(value):
    if value is not None and (not is_integer(value) or not 1 <= value <= 10):
        raise ValueError("评分必须是 1～10 的整数，或不评分")
    return value


def validate_comment(comment):
    if not isinstance(comment, dict) or "id" not in comment or "text" not in comment:
        raise ValueError("评论必须是包含 id 和 text 的字典")
    if not is_integer(comment["id"]) or comment["id"] <= 0:
        raise ValueError("评论 id 必须是正整数")
    validate_text(comment["text"], "评论", COMMENT_MIN, COMMENT_MAX)


def validate_song(song):
    required = {
        "id", "title", "artist", "album", "genre", "rating",
        "favorite", "play_count", "comments",
    }
    if not isinstance(song, dict) or not required <= song.keys():
        raise ValueError(f"歌曲必须包含字段：{', '.join(sorted(required))}")
    if not is_integer(song["id"]) or song["id"] <= 0:
        raise ValueError("歌曲 id 必须是正整数")
    validate_text(song["title"], "歌名", 1, TITLE_MAX)
    validate_text(song["artist"], "歌手", 1, ARTIST_MAX)
    validate_text(song["album"], "专辑", 0, ALBUM_MAX)
    validate_text(song["genre"], "流派", 0, GENRE_MAX)
    validate_rating(song["rating"])
    if type(song["favorite"]) is not bool:
        raise ValueError("favorite 必须是布尔值")
    if not is_integer(song["play_count"]) or song["play_count"] < 0:
        raise ValueError("play_count 必须是非负整数")
    if not isinstance(song["comments"], list):
        raise ValueError("comments 必须是列表")
    seen_ids = set()
    for comment in song["comments"]:
        validate_comment(comment)
        if comment["id"] in seen_ids:
            raise ValueError(f"重复评论 id：{comment['id']}")
        seen_ids.add(comment["id"])


def validate_library(library: list[dict]) -> None:
    if not isinstance(library, list):
        raise ValueError("JSON 最外层必须是列表")
    seen_ids = set()
    for position, song in enumerate(library, start=1):
        try:
            validate_song(song)
        except ValueError as error:
            raise ValueError(f"第 {position} 首歌曲：{error}") from error
        if song["id"] in seen_ids:
            raise ValueError(f"重复歌曲 id：{song['id']}")
        seen_ids.add(song["id"])


def find_song(library: list[dict], song_id: int) -> dict | None:
    for song in library:
        if song["id"] == song_id:
            return song
    return None


def next_song_id(library: list[dict]) -> int:
    return max((song["id"] for song in library), default=0) + 1


def add_song(library, title, artist, album="", genre="", rating=None):
    song = {
        "id": next_song_id(library), "title": title, "artist": artist,
        "album": album, "genre": genre, "rating": rating,
        "favorite": False, "play_count": 0, "comments": [],
    }
    validate_song(song)
    library.append(song)
    return song


def update_song(song, changes):
    allowed = {"title", "artist", "album", "genre", "rating"}
    if not set(changes) <= allowed:
        raise ValueError("不能修改这些歌曲字段")
    candidate = song.copy()
    candidate.update(changes)
    validate_song(candidate)
    changed = candidate != song
    if changed:
        song.update(changes)
    return changed


def delete_song(library: list[dict], song_id: int) -> bool:
    song = find_song(library, song_id)
    if song is None:
        return False
    library.remove(song)
    return True


def search_songs(library: list[dict], keyword: str) -> list[dict]:
    keyword = keyword.strip().casefold()
    if not keyword:
        raise ValueError("搜索关键词不能为空")
    fields = ("title", "artist", "album", "genre")
    return [
        song for song in library
        if any(keyword in song[field].casefold() for field in fields)
    ]


def filter_songs(library: list[dict], mode: str, genre: str = "") -> list[dict]:
    if mode == "genre":
        genre = genre.strip().casefold()
        if not genre:
            raise ValueError("流派关键词不能为空")
        return [song for song in library if genre in song["genre"].casefold()]

    if mode == "favorite":
        return [song for song in library if song["favorite"]]

    if mode == "unrated":
        return [song for song in library if song["rating"] is None]

    if mode == "commented":
        return [song for song in library if song["comments"]]

    raise ValueError("未知筛选方式")


def sort_songs(library: list[dict], mode: str) -> list[dict]:
    if mode == "title":
        return sorted(library, key=lambda song: song["title"].casefold())
    if mode == "rating":
        return sorted(library, key=lambda song: song["rating"] or 0, reverse=True)
    if mode == "plays":
        return sorted(library, key=lambda song: song["play_count"], reverse=True)
    raise ValueError("未知排序方式")


def set_favorite(song, favorite):
    if type(favorite) is not bool:
        raise ValueError("收藏状态必须是布尔值")
    changed = song["favorite"] != favorite
    song["favorite"] = favorite
    return changed


def record_play(song):
    song["play_count"] += 1
    return song["play_count"]


def find_comment(song, comment_id):
    for comment in song["comments"]:
        if comment["id"] == comment_id:
            return comment
    return None


def add_comment(song, text):
    text = validate_text(text, "评论", COMMENT_MIN, COMMENT_MAX)
    comment_id = max((item["id"] for item in song["comments"]), default=0) + 1
    comment = {"id": comment_id, "text": text}
    song["comments"].append(comment)
    return comment


def update_comment(song, comment_id, text):
    comment = find_comment(song, comment_id)
    if comment is None:
        return False
    text = validate_text(text, "评论", COMMENT_MIN, COMMENT_MAX)
    changed = comment["text"] != text
    comment["text"] = text
    return changed


def delete_comment(song, comment_id):
    comment = find_comment(song, comment_id)
    if comment is None:
        return False
    song["comments"].remove(comment)
    return True


def calculate_statistics(library: list[dict]) -> dict:
    ratings = [song["rating"] for song in library if song["rating"] is not None]
    top_rating = max(ratings) if ratings else None
    genres = {}
    for song in library:
        genre = song["genre"] or "未分类"
        genres[genre] = genres.get(genre, 0) + 1
    top_plays = max((song["play_count"] for song in library), default=None)
    return {
        "count": len(library),
        "favorites": sum(song["favorite"] for song in library),
        "total_plays": sum(song["play_count"] for song in library),
        "average_rating": sum(ratings) / len(ratings) if ratings else None,
        "top_rating": top_rating,
        "top_rated": [song for song in library if song["rating"] == top_rating]
        if top_rating is not None else [],
        "most_played": [song for song in library if song["play_count"] == top_plays]
        if top_plays is not None else [],
        "genres": genres,
    }
