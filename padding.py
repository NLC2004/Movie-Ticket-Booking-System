import sqlite3, datetime

sample = {
    "Beijing": {"movies": {"MovieA": ["Cinema1", "Cinema2"], "MovieB": ["Cinema3"]}},
    "Mumbai": {"movies": {"Dangal": ["Inox R-City"], "KGF": ["PVR Phoenix"]}},
    "Tokyo": {"movies": {"Kantara": ["INOX Orion"], "MovieC": ["PVR Forum"]}},
    "Hongkong": {"movies": {"HK Movie 1": ["Cinema HK1"], "HK Movie 2": ["Cinema HK2"]}},
}

conn = sqlite3.connect('ticketbox.db')
cur = conn.cursor()

# 清空旧数据，避免重复
cur.execute("DELETE FROM Cities")
for tbl in ("Chennai","Delhi","Beijing","Hongkong","Mumbai","Bangalore","Tokyo"):
    cur.execute(f"DELETE FROM {tbl}")
for day in ("Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"):
    cur.execute(f"DELETE FROM {day}")

for city, data in sample.items():
    movies = list(data["movies"].keys())
    cur.execute("INSERT INTO Cities (City, Movies) VALUES (?, ?)", (city, ",".join(movies)))
    for mv, ths in data["movies"].items():
        cur.execute(f"INSERT INTO {city} (movies, theatres) VALUES (?, ?)", (mv, ",".join(ths)))
        for th in ths:
            for offset in range(3):  # 未来3天示例库存
                d = (datetime.date.today() + datetime.timedelta(days=offset)).isoformat()
                daytable = datetime.datetime.fromisoformat(d).strftime("%A")
                cur.execute(f"INSERT INTO {daytable} (movie, theatre, date, seats) VALUES (?, ?, ?, ?)", (mv, th, d, "60"))
conn.commit()
print("done")
