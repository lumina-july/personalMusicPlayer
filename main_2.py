import csv
import json
import os


PROGRAM_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(PROGRAM_DIR, "songs_2.json")
CSV_FILE = os.path.join(PROGRAM_DIR, "songs_export.csv")


def is_integer(value):
    """bool 是 int 的子类，因此这里使用 type 做严格判断。"""
    return type(value) is int


def validate_library(data):
    """检查从 JSON 读取的数据是否符合当前程序的数据结构。"""
    if not isinstance(data, list):
        return False, "JSON 最外层必须是列表"

    seen_ids = set()

    for position, song in enumerate(data, start=1):
        if not isinstance(song, dict):
            return False, f"第 {position} 条记录不是字典"

        required_keys = {
            "id",
            "title",
            "artist",
            "album",
            "genre",
            "rating",
            "favorite",
            "play_count",
            "comments",
        }
        missing_keys = required_keys - set(song)
        if missing_keys:
            return False, f"第 {position} 条记录缺少字段：{sorted(missing_keys)}"

        song_id = song["id"]
        if not is_integer(song_id) or song_id <= 0:
            return False, f"第 {position} 条记录的 id 必须是正整数"
        if song_id in seen_ids:
            return False, f"发现重复 id：{song_id}"
        seen_ids.add(song_id)

        if not isinstance(song["title"], str) or not song["title"].strip():
            return False, f"第 {position} 条记录的 title 不能为空"
        if not isinstance(song["artist"], str) or not song["artist"].strip():
            return False, f"第 {position} 条记录的 artist 不能为空"
        if not isinstance(song["album"], str):
            return False, f"第 {position} 条记录的 album 必须是字符串"
        if not isinstance(song["genre"], str):
            return False, f"第 {position} 条记录的 genre 必须是字符串"

        rating = song["rating"]
        if rating is not None and (
            not is_integer(rating) or not 1 <= rating <= 10
        ):
            return False, f"第 {position} 条记录的 rating 必须是 1～10 或 null"

        if type(song["favorite"]) is not bool:
            return False, f"第 {position} 条记录的 favorite 必须是布尔值"

        play_count = song["play_count"]
        if not is_integer(play_count) or play_count < 0:
            return False, f"第 {position} 条记录的 play_count 必须是非负整数"

        comments = song["comments"]
        if not isinstance(comments, list):
            return False, f"第 {position} 条记录的 comments 必须是列表"

        seen_comment_ids = set()
        for comment_position, comment in enumerate(comments, start=1):
            if not isinstance(comment, dict):
                return False, (
                    f"第 {position} 条歌曲的第 {comment_position} 条评论不是字典"
                )
            if "id" not in comment or "text" not in comment:
                return False, (
                    f"第 {position} 条歌曲的第 {comment_position} 条评论"
                    "必须包含 id 和 text"
                )

            comment_id = comment["id"]
            if not is_integer(comment_id) or comment_id <= 0:
                return False, f"评论 id 必须是正整数：歌曲 id {song_id}"
            if comment_id in seen_comment_ids:
                return False, f"歌曲 id {song_id} 中有重复评论 id：{comment_id}"
            seen_comment_ids.add(comment_id)

            text = comment["text"]
            if not isinstance(text, str) or not 5 <= len(text.strip()) <= 1000:
                return False, f"歌曲 id {song_id} 的评论必须是 5～1000 个字符"

    return True, ""


def load_library(filename):
    """读取 JSON。文件不存在时创建空音乐库，损坏时返回 None。"""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("没有找到数据文件，将使用空音乐库。")
        return []
    except json.JSONDecodeError as error:
        print(
            "JSON 格式错误："
            f"第 {error.lineno} 行，第 {error.colno} 列，{error.msg}"
        )
        return None
    except OSError as error:
        print(f"读取文件失败：{error}")
        return None

    is_valid, message = validate_library(data)
    if not is_valid:
        print(f"数据内容不符合要求：{message}")
        return None

    return data


def save_library(library, filename):
    """保存 JSON；成功返回 True，失败返回 False。"""
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(library, file, ensure_ascii=False, indent=2)
    except OSError as error:
        print(f"保存失败：{error}")
        return False

    print(f"已保存 {len(library)} 首歌曲。")
    return True


def read_required_text(prompt):
    """反复询问，直到用户输入非空文本。"""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("输入不能为空，请重试。")


def read_integer(prompt, minimum=None, maximum=None, allow_blank=False):
    """读取整数，并根据参数检查范围。留空时可返回 None。"""
    while True:
        text = input(prompt).strip()

        if allow_blank and text == "":
            return None

        try:
            value = int(text)
        except ValueError:
            print("请输入整数。")
            continue

        if minimum is not None and value < minimum:
            print(f"数字不能小于 {minimum}。")
            continue
        if maximum is not None and value > maximum:
            print(f"数字不能大于 {maximum}。")
            continue

        return value


def read_yes_no(prompt):
    """读取 y/n，并返回 bool。"""
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("请输入 y 或 n。")


def next_song_id(library):
    """产生一个当前未使用的新 id。"""
    if not library:
        return 1
    song_ids = [song["id"] for song in library]
    return max(song_ids) + 1


def rating_text(rating):
    if rating is None:
        return "未评分"
    return f"{rating}/10"


def show_song(song):
    favorite_mark = "★" if song["favorite"] else " "
    album = song["album"] or "未知专辑"
    genre = song["genre"] or "未分类"
    print(
        f"[{song['id']}] {favorite_mark} {song['title']} - {song['artist']}"
        f" | {album} | {genre} | {rating_text(song['rating'])}"
        f" | 播放 {song['play_count']} 次 | 评论 {len(song['comments'])} 条"
    )


def show_songs(songs):
    if not songs:
        print("没有可显示的歌曲。")
        return

    for song in songs:
        show_song(song)


def find_song_by_id(library, song_id):
    for song in library:
        if song["id"] == song_id:
            return song
    return None


def choose_song(library):
    """让用户输入 id，并返回找到的歌曲；找不到时返回 None。"""
    if not library:
        print("音乐库是空的。")
        return None

    song_id = read_integer("请输入歌曲 id：", minimum=1)
    song = find_song_by_id(library, song_id)
    if song is None:
        print(f"没有找到 id 为 {song_id} 的歌曲。")
    return song


def add_song(library):
    title = read_required_text("歌名：")
    artist = read_required_text("歌手：")
    album = input("专辑（可以留空）：").strip()
    genre = input("流派（可以留空）：").strip()
    rating = read_integer(
        "评分（1～10，可以留空）：",
        minimum=1,
        maximum=10,
        allow_blank=True,
    )

    song = {
        "id": next_song_id(library),
        "title": title,
        "artist": artist,
        "album": album,
        "genre": genre,
        "rating": rating,
        "favorite": False,
        "play_count": 0,
        "comments": [],
    }
    library.append(song)
    print(f"已添加：{title} - {artist}（id：{song['id']}）")


def search_songs(library):
    keyword = input("搜索关键词：").strip().lower()
    if not keyword:
        print("搜索关键词不能为空。")
        return

    results = []
    for song in library:
        searchable_fields = (
            song["title"],
            song["artist"],
            song["album"],
            song["genre"],
        )
        for field in searchable_fields:
            if keyword in field.lower():
                results.append(song)
                break

    print(f"找到 {len(results)} 条结果：")
    show_songs(results)


def edit_song(library):
    song = choose_song(library)
    if song is None:
        return False

    print("直接回车表示保留原值；专辑或流派输入 - 表示清空。")

    title = input(f"歌名 [{song['title']}]：").strip()
    artist = input(f"歌手 [{song['artist']}]：").strip()
    album = input(f"专辑 [{song['album'] or '空'}]：").strip()
    genre = input(f"流派 [{song['genre'] or '空'}]：").strip()

    while True:
        rating = input(
            f"评分 [{rating_text(song['rating'])}]（1～10，0 清空，回车保留）："
        ).strip()
        if rating == "":
            new_rating = song["rating"]
            break
        if rating == "0":
            new_rating = None
            break
        try:
            new_rating = int(rating)
        except ValueError:
            print("评分必须是整数。")
            continue
        if 1 <= new_rating <= 10:
            break
        print("评分必须在 1～10 之间。")

    if title:
        song["title"] = title
    if artist:
        song["artist"] = artist
    if album:
        song["album"] = "" if album == "-" else album
    if genre:
        song["genre"] = "" if genre == "-" else genre
    song["rating"] = new_rating

    print("歌曲信息已修改。")
    show_song(song)
    return True


def delete_song(library):
    song = choose_song(library)
    if song is None:
        return False

    show_song(song)
    if not read_yes_no("确定删除这首歌吗？(y/n)："):
        print("已取消删除。")
        return False

    library.remove(song)
    print("歌曲已删除。")
    return True


def toggle_favorite(library):
    song = choose_song(library)
    if song is None:
        return False

    song["favorite"] = not song["favorite"]
    state = "已收藏" if song["favorite"] else "已取消收藏"
    print(f"{state}：{song['title']} - {song['artist']}")
    return True


def record_play(library):
    song = choose_song(library)
    if song is None:
        return False

    song["play_count"] += 1
    print(f"已记录播放：{song['title']}，累计 {song['play_count']} 次。")
    return True


def read_comment_text(prompt):
    """读取 5～1000 个字符的评论文本。"""
    while True:
        text = input(prompt).strip()
        length = len(text)
        if length < 5:
            print("评论不能少于 5 个字符。")
            continue
        if length > 1000:
            print("评论不能超过 1000 个字符。")
            continue
        return text


def next_comment_id(song):
    comments = song["comments"]
    if not comments:
        return 1
    comment_ids = [comment["id"] for comment in comments]
    return max(comment_ids) + 1


def find_comment_by_id(song, comment_id):
    for comment in song["comments"]:
        if comment["id"] == comment_id:
            return comment
    return None


def show_comments(song):
    comments = song["comments"]
    if not comments:
        print("这首歌还没有评论。")
        return

    print(f"《{song['title']}》的评论：")
    for comment in comments:
        print(f"  [{comment['id']}] {comment['text']}")


def choose_comment(song):
    if not song["comments"]:
        print("这首歌还没有评论。")
        return None

    show_comments(song)
    comment_id = read_integer("请输入评论 id：", minimum=1)
    comment = find_comment_by_id(song, comment_id)
    if comment is None:
        print(f"没有找到 id 为 {comment_id} 的评论。")
    return comment


def add_comment(song):
    text = read_comment_text("请输入评论：")
    comment = {
        "id": next_comment_id(song),
        "text": text,
    }
    song["comments"].append(comment)
    print(f"评论已添加，id：{comment['id']}。")
    return True


def edit_comment(song):
    comment = choose_comment(song)
    if comment is None:
        return False

    print(f"原评论：{comment['text']}")
    comment["text"] = read_comment_text("请输入修改后的评论：")
    print("评论已修改。")
    return True


def delete_comment(song):
    comment = choose_comment(song)
    if comment is None:
        return False

    if not read_yes_no(f"确定删除评论“{comment['text']}”吗？(y/n)："):
        print("已取消删除评论。")
        return False

    song["comments"].remove(comment)
    print("评论已删除。")
    return True


def manage_comments(library):
    song = choose_song(library)
    if song is None:
        return False

    has_changes = False

    while True:
        print(f"\n=== 管理《{song['title']}》的评论 ===")
        print("1. 查看评论")
        print("2. 添加评论")
        print("3. 修改评论")
        print("4. 删除评论")
        print("0. 返回主菜单")
        choice = input("请选择操作：").strip()

        if choice == "1":
            show_comments(song)
        elif choice == "2":
            if add_comment(song):
                has_changes = True
        elif choice == "3":
            if edit_comment(song):
                has_changes = True
        elif choice == "4":
            if delete_comment(song):
                has_changes = True
        elif choice == "0":
            return has_changes
        else:
            print("无效选项，请重新输入。")


def title_sort_key(song):
    return song["title"].lower()


def rating_sort_key(song):
    if song["rating"] is None:
        return 0
    return song["rating"]


def play_count_sort_key(song):
    return song["play_count"]


def filter_and_sort_songs(library):
    if not library:
        print("音乐库是空的。")
        return

    print("1. 按流派筛选")
    print("2. 只看收藏")
    print("3. 只看未评分歌曲")
    print("4. 按歌名排序")
    print("5. 按评分从高到低排序")
    print("6. 按播放次数从高到低排序")
    choice = input("请选择：").strip()

    if choice == "1":
        genre = input("请输入流派关键词：").strip().lower()
        if not genre:
            print("流派关键词不能为空。")
            return
        results = [song for song in library if genre in song["genre"].lower()]
    elif choice == "2":
        results = [song for song in library if song["favorite"]]
    elif choice == "3":
        results = [song for song in library if song["rating"] is None]
    elif choice == "4":
        results = sorted(library, key=title_sort_key)
    elif choice == "5":
        # 未评分用 0 参与排序，因此排在已评分歌曲后面。
        results = sorted(
            library,
            key=rating_sort_key,
            reverse=True,
        )
    elif choice == "6":
        results = sorted(
            library,
            key=play_count_sort_key,
            reverse=True,
        )
    else:
        print("无效选项。")
        return

    show_songs(results)


def show_statistics(library):
    if not library:
        print("音乐库是空的，暂无统计数据。")
        return

    favorite_count = 0
    total_plays = 0
    ratings = []
    genre_counts = {}

    for song in library:
        if song["favorite"]:
            favorite_count += 1
        total_plays += song["play_count"]
        if song["rating"] is not None:
            ratings.append(song["rating"])

        genre = song["genre"] or "未分类"
        genre_counts[genre] = genre_counts.get(genre, 0) + 1

    print(f"歌曲总数：{len(library)}")
    print(f"收藏数量：{favorite_count}")
    print(f"累计播放：{total_plays}")

    if ratings:
        average = sum(ratings) / len(ratings)
        print(f"平均评分：{average:.2f}/10")

        highest_rating = max(ratings)
        highest_songs = []
        for song in library:
            if song["rating"] == highest_rating:
                highest_songs.append(song)

        print(f"最高评分歌曲（{highest_rating}/10）：")
        for song in highest_songs:
            print(f"  {song['title']} - {song['artist']}")
    else:
        print("平均评分：暂无评分")
        print("最高评分歌曲：暂无评分")

    most_played = max(library, key=play_count_sort_key)
    print(
        f"播放最多：{most_played['title']} - {most_played['artist']} "
        f"（{most_played['play_count']} 次）"
    )

    print("流派分布：")
    for genre, count in sorted(genre_counts.items()):
        print(f"  {genre}：{count}")


def export_csv(library, filename):
    fieldnames = [
        "id",
        "title",
        "artist",
        "album",
        "genre",
        "rating",
        "favorite",
        "play_count",
        "comments",
    ]

    try:
        with open(filename, "w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for song in library:
                csv_row = song.copy()
                comment_texts = []
                for comment in song["comments"]:
                    comment_texts.append(comment["text"])
                csv_row["comments"] = " | ".join(comment_texts)
                writer.writerow(csv_row)
    except OSError as error:
        print(f"CSV 导出失败：{error}")
        return False

    print(f"已导出到：{filename}")
    return True


def show_menu():
    print("\n=== Personal Music Library Analyzer — Stage 1 ===")
    print("1. 查看全部歌曲")
    print("2. 添加歌曲")
    print("3. 搜索歌曲")
    print("4. 修改歌曲")
    print("5. 删除歌曲")
    print("6. 筛选或排序")
    print("7. 收藏或取消收藏")
    print("8. 记录一次播放")
    print("9. 管理评论")
    print("10. 查看统计")
    print("11. 导出 CSV")
    print("12. 保存")
    print("0. 退出")


def ask_to_exit(library, has_unsaved_changes):
    """返回 True 表示退出，False 表示继续运行。"""
    if not has_unsaved_changes:
        return True

    should_save = read_yes_no("有尚未保存的修改，退出前保存吗？(y/n)：")
    if should_save:
        return save_library(library, DATA_FILE)
    return read_yes_no("不保存会丢失本次修改，仍然退出吗？(y/n)：")


def run_program():
    library = load_library(DATA_FILE)
    if library is None:
        print("为避免覆盖原数据，程序不会进入编辑状态。")
        return

    has_unsaved_changes = False

    while True:
        show_menu()
        choice = input("请选择操作：").strip()

        if choice == "1":
            show_songs(library)
        elif choice == "2":
            add_song(library)
            has_unsaved_changes = True
        elif choice == "3":
            search_songs(library)
        elif choice == "4":
            if edit_song(library):
                has_unsaved_changes = True
        elif choice == "5":
            if delete_song(library):
                has_unsaved_changes = True
        elif choice == "6":
            filter_and_sort_songs(library)
        elif choice == "7":
            if toggle_favorite(library):
                has_unsaved_changes = True
        elif choice == "8":
            if record_play(library):
                has_unsaved_changes = True
        elif choice == "9":
            if manage_comments(library):
                has_unsaved_changes = True
        elif choice == "10":
            show_statistics(library)
        elif choice == "11":
            export_csv(library, CSV_FILE)
        elif choice == "12":
            if save_library(library, DATA_FILE):
                has_unsaved_changes = False
        elif choice == "0":
            if ask_to_exit(library, has_unsaved_changes):
                print("程序已退出。")
                break
        else:
            print("无效选项，请重新输入。")


if __name__ == "__main__":
    run_program()