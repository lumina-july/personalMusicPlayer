"""命令行交互；把用户输入转成 core 的参数，并显示结果。"""

from pathlib import Path

import core
import storage


PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "songs_2.json"
CSV_FILE = PROJECT_DIR / "songs_export.csv"  


def read_text(prompt, minimum=0, maximum=100):
    while True:
        value = input(prompt)
        try:
            return core.validate_text(value, "输入内容", minimum, maximum)
        except ValueError as error:
            print(error)


def read_integer(prompt, minimum=None, maximum=None, allow_blank=False):
    while True:
        text = input(prompt).strip()
        if allow_blank and not text:
            return None
        ''' 注意如果用了none就不能用if not 返回值了，因为0也会被判定为False，所以要用is None判断
            正确例子：
            num = read_integer("数字：", allow_blank=True)
            if num is None:
            print("用户没填")
            else:
            print(f"用户输入数字：{num}")'''
        try:
            value = int(text)
        except ValueError:
            print("请输入整数。")
            continue
        if minimum is not None and value < minimum:
            print(f"数字不能小于 {minimum}。")
        elif maximum is not None and value > maximum:
            print(f"数字不能大于 {maximum}。")
        else:
            return value


def read_yes_no(prompt):
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("请输入 y 或 n。")


def rating_text(rating):
    return "未评分" if rating is None else f"{rating}/10"


def show_songs(songs):
    if not songs:
        print("没有可显示的歌曲。")
        return
    for number, song in enumerate(songs, start=1):
        mark = "★" if song["favorite"] else " "
        print(
            f"序号 {number} | ID {song['id']} | {mark} {song['title']} - {song['artist']}"
            f" | {song['album'] or '未知专辑'} | {song['genre'] or '未分类'}"
            f" | {rating_text(song['rating'])} | 播放 {song['play_count']} 次"
            f" | 评论 {len(song['comments'])} 条"
        )


def choose_song(library):
    if not library:
        print("音乐库是空的。")
        return None
    song_id = read_integer("请输入歌曲 ID（不是显示序号）：", minimum=1)
    song = core.find_song(library, song_id)
    if song is None:
        print(f"没有找到 ID 为 {song_id} 的歌曲。")
    return song


def add_song(library):
    title = read_text("歌名：", 1, core.TITLE_MAX)
    artist = read_text("歌手：", 1, core.ARTIST_MAX)
    album = read_text("专辑（可留空）：", 0, core.ALBUM_MAX)
    genre = read_text("流派（可留空）：", 0, core.GENRE_MAX)
    rating = read_integer("评分（1～10，可留空）：", 1, 10, allow_blank=True)
    song = core.add_song(library, title, artist, album, genre, rating)
    print(f"已添加：{song['title']}，ID {song['id']}。")
    return True


def edit_song(library):
    song = choose_song(library)
    if song is None:
        return False
    print("回车保留原值；专辑或流派输入 - 清空。")
    changes = {}
    """空字典，用来存放本次用户想要修改的字段和新值,不改不放"""
    for field, label, maximum in (
        ("title", "歌名", core.TITLE_MAX),
        '''键会在song[field]中，变成值看'''
        ("artist", "歌手", core.ARTIST_MAX),
        ("album", "专辑", core.ALBUM_MAX),
        ("genre", "流派", core.GENRE_MAX),
    ):
        while True:
            text = input(f"{label} [{song[field] or '空'}]：").strip()
            '''先打印原名；
               A or B 规则：A 是空字符串""/None 时，返回 B；
               否则返回 A。用来兜底显示 “空”。'''
            if not text:
                break
            if text == "-" and field in ("album", "genre"):
                changes[field] = ""
                '''之前设定了专辑和流派可以清空，
                   所以这里如果用户输入 - 就把对应字段设为空字符串'''
                break
            try:
                changes[field] = core.validate_text(text, label, 1, maximum)
                break
            except ValueError as error:
                print(error)

    while True:
        text = input(
            f"评分 [{rating_text(song['rating'])}]（回车保留，0 清空，1～10 设置）："
        ).strip()
        if text == "":
            break
        if text == "0":
            changes["rating"] = None
            break
        try:
            value = int(text)
            changes["rating"] = core.validate_rating(value)
            break
        except ValueError as error:
            print(error)

    changed = core.update_song(song, changes)
    print("歌曲已修改。" if changed else "歌曲信息没有变化。")
    return changed


def delete_song(library):
    song = choose_song(library)
    if song is None:
        return False
    show_songs([song])
    if not read_yes_no("确定删除这首歌吗？(y/n)："):
        print("已取消删除。")
        return False
    core.delete_song(library, song["id"])
    print("歌曲已删除。原 ID 不会使其他歌曲重新编号。")
    return True


def show_comments(song):
    if not song["comments"]:
        print("这首歌还没有评论。")
    else:
        for comment in song["comments"]:
            print(f"评论 ID {comment['id']}：{comment['text']}")


def manage_comments(library):
    song = choose_song(library)
    if song is None:
        return False
    changed = False
    while True:
        print("\n1. 查看评论  2. 添加评论  3. 修改评论  4. 删除评论  0. 返回")
        choice = input("请选择：").strip()
        if choice == "0":
            return changed
        if choice == "1":
            show_comments(song)
        elif choice == "2":
            text = read_text("评论：", core.COMMENT_MIN, core.COMMENT_MAX)
            comment = core.add_comment(song, text)
            print(f"已添加评论 ID {comment['id']}。")
            changed = True
        elif choice in ("3", "4"):
            show_comments(song)
            if not song["comments"]:
                continue
            comment_id = read_integer("评论 ID：", minimum=1)
            comment = core.find_comment(song, comment_id)
            if comment is None:
                print("没有找到该评论。")
                continue
            if choice == "3":
                text = read_text("新评论：", core.COMMENT_MIN, core.COMMENT_MAX)
                if core.update_comment(song, comment_id, text):
                    changed = True
                print("评论已修改。")
            elif read_yes_no("确定删除这条评论吗？(y/n)："):
                core.delete_comment(song, comment_id)
                changed = True
                print("评论已删除。")
        else:
            print("无效选项。")


def filter_and_sort(library):
    print("1. 流派筛选  2. 只看收藏  3. 只看未评分")
    print("4. 只看有评论  5. 按歌名排序  6. 按评分排序")
    print("7. 按播放次数排序")

    choice = input("请选择：").strip()

    try:
        if choice == "1":
            results = core.filter_songs(
                library,
                "genre",
                input("流派关键词："),
            )
        elif choice in ("2", "3", "4"):
            mode = {
                "2": "favorite",
                "3": "unrated",
                "4": "commented",
            }[choice]
            results = core.filter_songs(library, mode)
        elif choice in ("5", "6", "7"):
            mode = {
                "5": "title",
                "6": "rating",
                "7": "plays",
            }[choice]
            results = core.sort_songs(library, mode)
        else:
            print("无效选项。")
            return

        show_songs(results)

    except ValueError as error:
        print(error)


def show_statistics(library):
    stats = core.calculate_statistics(library)
    print(f"歌曲总数：{stats['count']}")
    if not library:
        return
    print(f"收藏数量：{stats['favorites']}")
    print(f"累计播放：{stats['total_plays']}")
    average = stats["average_rating"]
    print(f"平均评分：{average:.2f}/10" if average is not None else "平均评分：暂无评分")
    if stats["top_rated"]:
        print(f"最高评分歌曲（{stats['top_rating']}/10）：")
        show_songs(stats["top_rated"])
    else:
        print("最高评分歌曲：暂无评分")
    print("播放最多：")
    show_songs(stats["most_played"])
    print("流派分布：")
    for genre, count in sorted(stats["genres"].items()):
        print(f"  {genre}：{count}")


def save_with_message(library, filename):
    try:
        storage.save_library(library, filename)
    except (OSError, ValueError) as error:
        print(f"保存失败：{error}")
        return False
    print(f"已保存 {len(library)} 首歌曲。")
    return True


def ask_to_exit(library, dirty, filename):
    if not dirty:
        return True
    if read_yes_no("有尚未保存的修改，退出前保存吗？(y/n)："):
        return save_with_message(library, filename)
    return read_yes_no("不保存会丢失本次修改，仍然退出吗？(y/n)：")


def show_menu():
    print("\n=== Personal Music Library Analyzer — Stage 2 ===")
    print("1. 查看全部  2. 添加  3. 搜索  4. 修改  5. 删除")
    print("6. 筛选/排序  7. 收藏  8. 记录播放  9. 评论")
    print("10. 统计  11. 导出 CSV  12. 保存  0. 退出")


def run_program(data_file=DATA_FILE, csv_file=CSV_FILE):
    try:
        load_result = storage.load_library(data_file)
        library = load_result.songs
    except (storage.LibraryDataError, OSError) as error:
        print(f"无法读取音乐库：{error}")
        print("为避免覆盖原数据，程序已停止。")
        return
    if load_result.migrated_count:
        print(f"已迁移 {load_result.migrated_count} 首歌曲。")
    skipped_count = len(load_result.skipped or [])
    if skipped_count:
        print(f"已跳过 {skipped_count} 条无法迁移的记录。")
        print(f"错误报告：{load_result.error_report}")
    dirty = False
    while True:
        show_menu()
        choice = input("请选择操作：").strip()
        if choice == "1":
            show_songs(library)
        elif choice == "2":
            dirty = add_song(library) or dirty
        elif choice == "3":
            try:
                show_songs(core.search_songs(library, input("搜索关键词：")))
            except ValueError as error:
                print(error)
        elif choice == "4":
            dirty = edit_song(library) or dirty
        elif choice == "5":
            dirty = delete_song(library) or dirty
        elif choice == "6":
            filter_and_sort(library)
        elif choice == "7":
            song = choose_song(library)
            if song is not None:
                dirty = core.set_favorite(song, not song["favorite"]) or dirty
                print("收藏状态已切换。")
        elif choice == "8":
            song = choose_song(library)
            if song is not None:
                count = core.record_play(song)
                dirty = True
                print(f"已记录播放，累计 {count} 次。")
        elif choice == "9":
            dirty = manage_comments(library) or dirty
        elif choice == "10":
            show_statistics(library)
        elif choice == "11":
            try:
                storage.export_csv(library, csv_file)
                print(f"已导出：{csv_file}")
            except (OSError, ValueError) as error:
                print(f"导出失败：{error}")
        elif choice == "12":
            if save_with_message(library, data_file):
                dirty = False
        elif choice == "0":
            if ask_to_exit(library, dirty, data_file):
                print("程序已退出。")
                return
        else:
            print("无效选项。")
