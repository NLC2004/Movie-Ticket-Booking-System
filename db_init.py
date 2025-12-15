import datetime
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ticketbox.db"


def create_tables(conn: sqlite3.Connection) -> None:
    """创建规范表：User/Movie/City/Theatre/Schedule/SeatBooking/Order。"""
    cur = conn.cursor()
    # 用户表（与原 user 表兼容）
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            mobile_number TEXT,
            email TEXT
        )
        """
    )
    # 城市
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS city (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
        """
    )
    # 影院
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS theatre (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            city_id INTEGER,
            FOREIGN KEY(city_id) REFERENCES city(id)
        )
        """
    )
    # 电影
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            rating REAL,
            poster_path TEXT,
            summary TEXT
        )
        """
    )
    # 排期
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            theatre_id INTEGER,
            show_date TEXT,
            total_seats INTEGER DEFAULT 60,
            available_seats INTEGER DEFAULT 60,
            FOREIGN KEY(movie_id) REFERENCES movies(id),
            FOREIGN KEY(theatre_id) REFERENCES theatre(id)
        )
        """
    )
    # 座位占用
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS seat_booking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER,
            seat_code TEXT,
            FOREIGN KEY(schedule_id) REFERENCES schedule(id)
        )
        """
    )
    # 订单
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            schedule_id INTEGER,
            seat_count INTEGER,
            amount REAL,
            status TEXT,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(schedule_id) REFERENCES schedule(id)
        )
        """
    )
    conn.commit()


def seed_sample_data(conn: sqlite3.Connection) -> None:
    """
    按规范表填充示例数据：
    - 插入城市、影院
    - 插入电影
    - 生成未来 3 天的排期
    """
    sample = {
        "Beijing": {
            "theatres": ["Cinema1", "Cinema2", "Cinema3"],
            "movies": {
                "MovieA": {
                    "rating": 8.7,
                    "poster_path": "static/images/poster1.jpg",
                    "summary": "Beijing MovieA 简介",
                },
                "MovieB": {
                    "rating": 8.2,
                    "poster_path": "static/images/poster2.jpg",
                    "summary": "Beijing MovieB 简介",
                },
            },
        },
        "Mumbai": {
            "theatres": ["Inox R-City", "PVR Phoenix"],
            "movies": {
                "Dangal": {
                    "rating": 8.4,
                    "poster_path": "static/images/poster3.jpg",
                    "summary": "Mumbai Dangal 简介",
                },
                "KGF": {
                    "rating": 7.9,
                    "poster_path": "static/images/poster4.jpg",
                    "summary": "Mumbai KGF 简介",
                },
            },
        },
        "Tokyo": {
            "theatres": ["INOX Orion", "PVR Forum"],
            "movies": {
                "Kantara": {
                    "rating": 8.1,
                    "poster_path": "static/images/poster5.jpg",
                    "summary": "Tokyo Kantara 简介",
                },
                "MovieC": {
                    "rating": 7.5,
                    "poster_path": "static/images/poster6.jpg",
                    "summary": "Tokyo MovieC 简介",
                },
            },
        },
        "Hongkong": {
            "theatres": ["Cinema HK1", "Cinema HK2"],
            "movies": {
                "HK Movie 1": {
                    "rating": 8.0,
                    "poster_path": "static/images/poster7.jpg",
                    "summary": "Hongkong Movie 1 简介",
                },
                "HK Movie 2": {
                    "rating": 7.8,
                    "poster_path": "static/images/poster8.jpg",
                    "summary": "Hongkong Movie 2 简介",
                },
            },
        },
    }

    cur = conn.cursor()
    # 清空示例表，防止重复
    for tbl in ("city", "theatre", "movies", "schedule", "seat_booking"):
        cur.execute(f"DELETE FROM {tbl}")
    conn.commit()

    movie_ids = {}
    # 插入城市/影院/电影，并生成排期
    for city_name, cdata in sample.items():
        cur.execute("INSERT INTO city (name) VALUES (?)", (city_name,))
        city_id = cur.lastrowid
        # 影院
        theatre_ids = []
        for th in cdata.get("theatres", []):
            cur.execute("INSERT INTO theatre (name, city_id) VALUES (?, ?)", (th, city_id))
            theatre_ids.append(cur.lastrowid)
        # 电影
        for title, meta in cdata.get("movies", {}).items():
            if title not in movie_ids:
                cur.execute(
                    "INSERT INTO movies (title, rating, poster_path, summary) VALUES (?, ?, ?, ?)",
                    (title, meta.get("rating"), meta.get("poster_path"), meta.get("summary")),
                )
                movie_ids[title] = cur.lastrowid
            movie_id = movie_ids[title]
            # 生成未来 3 天排期
            for th_id in theatre_ids:
                for offset in range(3):
                    d = (datetime.date.today() + datetime.timedelta(days=offset)).isoformat()
                    cur.execute(
                        "INSERT INTO schedule (movie_id, theatre_id, show_date, total_seats, available_seats) VALUES (?, ?, ?, ?, ?)",
                        (movie_id, th_id, d, 60, 60),
                    )
    conn.commit()


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    seed_sample_data(conn)
    print(f"初始化完成，示例数据已写入 city/theatre/movies/schedule，数据库：{DB_PATH}")


if __name__ == "__main__":
    main()
