from flask import Flask, render_template, request, redirect, g, session 
import sqlite3 
import os 
from flask_mail import Mail, Message 
from flask_sqlalchemy import SQLAlchemy 
from flask_admin import Admin 
from flask_admin.contrib.sqla import ModelView 
from flask_admin.menu import MenuLink
from random import randint
import time, datetime 



app = Flask(__name__) 
 
app.config['DATABASE'] = os.path.join(app.root_path, 'ticketbox.db') 
# otp mail connection 
app.config["MAIL_SERVER"] = 'smtp.gmail.com' 
app.config["MAIL_PORT"] = 465 
app.config["MAIL_USERNAME"] = 'ticketbox4567@gmail.com' 
app.config['MAIL_PASSWORD'] = 'jbbbmerdghkmkcsd' 
app.config['MAIL_USE_TLS'] = False 
app.config['MAIL_USE_SSL'] = True 
 
mail = Mail(app) 

#flask-sqlalchemy connection 
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{app.config['DATABASE']}" 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
app.config['SECRET_KEY'] = 'tisasecret' 
 
# 邮件发送安全包装，避免网络超时导致 500
def send_mail_safely(message):
    try:
        mail.send(message)
    except Exception as e:
        # 开发环境网络不通时打印错误并继续流程
        print("Mail send failed:", e)
 
# runtime state (simple globals; consider sessions for production)
city_id = None
movie_id = None
theatre_id = None
schedule_id = None
amount_pay = 0 
 
def get_db(): 
    """Return a sqlite3 connection stored on the flask app context.""" 
    if 'db_conn' not in g: 
        g.db_conn = sqlite3.connect(app.config['DATABASE']) 
        g.db_conn.row_factory = sqlite3.Row 
    return g.db_conn 
 
@app.teardown_appcontext 
def close_db(exception): 
    db_conn = g.pop('db_conn', None) 
    if db_conn is not None: 
        db_conn.close() 
 
db = SQLAlchemy(app) 
 
#admin module 
admin = Admin(app) 
 
#tables in admin 
class User(db.Model): 
    __tablename__ = "user" 
    id = db.Column(db.Integer, primary_key=True) 
    username = db.Column(db.String(30)) 
    password = db.Column(db.String(8)) 
    mobile_number = db.Column(db.BigInteger) 
    email = db.Column(db.String(50)) 
 
admin.add_view(ModelView(User, db.session, category="Users")) 
 
class Administrator(db.Model): 
    __tablename__ = "Administrator" 
    id = db.Column(db.Integer, primary_key=True) 
    admin_name = db.Column(db.String(30)) 
    admin_password = db.Column(db.String(8)) 
    admin_email = db.Column(db.String(50)) 
 
admin.add_view(ModelView(Administrator, db.session, category="Admins")) 
 
class User_Log(db.Model): 
    __tablename__ = "User__Log" 
    id = db.Column(db.Integer, primary_key=True) 
    username = db.Column(db.String(30)) 
    login_time = db.Column(db.DateTime) 
    city_selected = db.Column(db.String(20)) 
    movie_selected = db.Column(db.String(50)) 
    theatre_selected = db.Column(db.String(50)) 
    date_selected = db.Column(db.DateTime) 
    number_of_tickets = db.Column(db.String(10)) 
    seats_selected = db.Column(db.String(100)) 
    amount_paid = db.Column(db.Integer) 
    bank = db.Column(db.String(30)) 
    card_type = db.Column(db.String(30)) 
    card_number = db.Column(db.String(25)) 
    expiration_date = db.Column(db.String(5)) 
    cvv_number = db.Column(db.String(3)) 
    name_on_card = db.Column(db.String(50)) 
 
admin.add_view(ModelView(User_Log, db.session, category="Users")) 
 
class Admin_Login(db.Model):
    __tablename__ = "Admin__Login"
    id = db.Column(db.Integer, primary_key=True)
    admin_name = db.Column(db.String(30))
    login_time = db.Column(db.DateTime)

admin.add_view(ModelView(Admin_Login, db.session, category="Admins"))

class Movie(db.Model):
    __tablename__ = "movies"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Float)
    poster_path = db.Column(db.String(500))
    summary = db.Column(db.Text)

admin.add_view(ModelView(Movie, db.session, category="Content"))

class City(db.Model):
    __tablename__ = "city"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)

admin.add_view(ModelView(City, db.session, category="Locations"))

class Theatre(db.Model):
    __tablename__ = "theatre"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    city_id = db.Column(db.Integer, db.ForeignKey("city.id"))

admin.add_view(ModelView(Theatre, db.session, category="Locations"))

class Schedule(db.Model):
    __tablename__ = "schedule"
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id"))
    theatre_id = db.Column(db.Integer, db.ForeignKey("theatre.id"))
    show_date = db.Column(db.String(20))  # ISO date
    total_seats = db.Column(db.Integer, default=60)
    available_seats = db.Column(db.Integer, default=60)

admin.add_view(ModelView(Schedule, db.session, category="Schedules"))

class SeatBooking(db.Model):
    __tablename__ = "seat_booking"
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id"))
    seat_code = db.Column(db.String(10))

admin.add_view(ModelView(SeatBooking, db.session, category="Schedules"))

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedule.id"))
    seat_count = db.Column(db.Integer)
    amount = db.Column(db.Float)
    status = db.Column(db.String(30))

admin.add_view(ModelView(Order, db.session, category="Orders"))
admin.add_link(MenuLink(name="订单查询", category="Orders", url="/orders"))

# 默认管理员与后台保护
def ensure_default_admin():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM Administrator WHERE admin_name = ?", ("admin1",))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO Administrator (admin_name, admin_password, admin_email) VALUES (?, ?, ?)",
            ("admin1", "ljy19800101", "admin1@example.com"),
        )
        conn.commit()

def ensure_orders_schema():
    """迁移旧 orders 表到新结构（seat_count, amount, status）。"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(orders)")
    cols = [c[1] for c in cur.fetchall()]
    needed = {"seat_count", "amount", "status"}
    if needed.issubset(set(cols)):
        return
    cur.execute("ALTER TABLE orders RENAME TO orders_old")
    cur.execute(
        """
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            schedule_id INTEGER,
            seat_count INTEGER,
            amount REAL,
            status TEXT
        )
        """
    )
    try:
        cur.execute("SELECT id, user_id, schedule_id, seats, amount_paid FROM orders_old")
        rows = cur.fetchall()
        for oid, uid, sid, seats, amt in rows:
            seat_count = 0
            if seats:
                seat_count = len([s for s in str(seats).split(",") if s])
            cur.execute(
                "INSERT INTO orders (id, user_id, schedule_id, seat_count, amount, status) VALUES (?, ?, ?, ?, ?, ?)",
                (oid, uid, sid, seat_count, amt, "paid"),
            )
    except Exception:
        pass
    conn.commit()
    cur.execute("DROP TABLE IF EXISTS orders_old")
    conn.commit()

@app.before_request
def protect_admin():
    if request.path.startswith("/admin") and not request.path.startswith("/admin-login"):
        if session.get("is_admin"):
            return None
        if request.path.startswith("/admin/static"):
            return None
        return redirect("/admin-login")


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    # 每次进入管理员登录清理旧会话
    session.pop("is_admin", None)
    session.pop("admin_name", None)
    if request.method == "POST":
        name = request.form.get("username")
        pwd = request.form.get("password")
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT admin_email FROM Administrator WHERE admin_name = ? AND admin_password = ?",
            (name, pwd),
        )
        row = cur.fetchone()
        if row:
            session["is_admin"] = True
            session["admin_name"] = name
            return redirect("/admin/")
        return "<center><h1>管理员账号或密码错误</h1><br><a href='/admin-login'>返回</a></center>"
    return """
    <html><body style='font-family:Arial; display:flex; justify-content:center; align-items:center; height:100vh; background:#111; color:#fff;'>
    <form method='POST' style='background:rgba(0,0,0,0.6); padding:30px; border-radius:8px;'>
      <h2>Admin Login</h2>
      <div><label>Username:</label><br><input name='username' required></div>
      <div style='margin-top:10px;'><label>Password:</label><br><input name='password' type='password' required></div>
      <div style='margin-top:15px;'><button type='submit'>Login</button></div>
    </form>
    </body></html>
    """


@app.route("/orders", methods=["GET"])
def order_search():
    search_type = request.args.get("type", "")
    keyword = request.args.get("q", "")
    conn = get_db()
    cur = conn.cursor()
    base_query = """
        SELECT 
            o.id,
            u.username,
            m.title,
            c.name as city_name,
            t.name as theatre_name,
            s.show_date,
            o.seat_count,
            o.amount,
            o.status
        FROM orders o
        LEFT JOIN user u ON o.user_id = u.id
        LEFT JOIN schedule s ON o.schedule_id = s.id
        LEFT JOIN movies m ON s.movie_id = m.id
        LEFT JOIN theatre t ON s.theatre_id = t.id
        LEFT JOIN city c ON t.city_id = c.id
    """
    conditions = []
    params = []
    if search_type == "user" and keyword:
        conditions.append("u.username LIKE ?")
        params.append(f"%{keyword}%")
    elif search_type == "movie" and keyword:
        conditions.append("m.title LIKE ?")
        params.append(f"%{keyword}%")
    elif search_type == "date" and keyword:
        conditions.append("s.show_date = ?")
        params.append(keyword)
    query = base_query
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY o.id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "username": r[1],
            "title": r[2],
            "city": r[3],
            "theatre": r[4],
            "show_date": r[5],
            "seat_count": r[6],
            "amount": r[7],
            "status": r[8],
        })
    return render_template("order_search.html", results=results, search_type=search_type, keyword=keyword)

with app.app_context():
    db.create_all()
    ensure_default_admin()
    ensure_orders_schema()

# homepage render 
@app.route('/') 
def home(): 
    return render_template('home.html') 
 
# sign up page render + OTP generation 
@app.route('/signup', methods=['GET', 'POST']) 
def signup(): 
    if request.method == "POST": 
        details = request.form 
        global username 
        username = details['uname'] 
        passw = details['psswd'] 
        mobile = details['num'] 
        global email 
        email = details['em'] 
        confirm = details['pass'] 
        global otp 
        otp = randint(000000, 999999) 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute( 
            "SELECT * FROM user where username = ?", (username,)) 
        name = cur.fetchone() 
        if name is None: 
            if len(passw) == 8: 
                if confirm == passw: 
                    cur.execute( 
                        "INSERT INTO user(Username, Password, Mobile_number, Email) VALUES (?, ?, ?, ?)", (username, passw, mobile, email)) 
                    conn.commit() 
                    cur.close() 
                    message = Message( 
                        'Verfication code for TicketBox', sender='ticketbox4567@gmail.com', recipients=[email]) 
                    message.body = "Your 6-digit OTP code is " + str(otp) 
                    send_mail_safely(message) 
                    return render_template('verification.html') 
                else: 
                    return "<center><h1>Password was not confirmed</h1><br><a href='http://127.0.0.1:5000/signup'>Back to Sign Up</a></h1></center>" 
            else: 
                return "<center><h1>Password is not 8 characters</h1><br><a href='http://127.0.0.1:5000/signup'>Back to Sign Up</a></h1></center>" 
        else: 
            return "<center><h1>Username is already taken<br><a href='http://127.0.0.1:5000/signup'>Back to Sign Up</a></h1></center>" 
    return render_template('signup.html') 
 
# cancellation login request 
@app.route('/cancellationlogin', methods=['POST', 'GET']) 
def cancellationlogin(): 
    if request.method == 'POST': 
        del_usname = request.form["del_username"] 
        del_pass = request.form["del_password"] 
        del_now = time.strftime('%Y-%m-%d %H:%M:%S') 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute("SELECT * FROM user WHERE username = ? and password = ?",(del_usname,del_pass)) 
        global query_del 
        query_del = cur.fetchone() 
        if query_del is not None:
            cur.execute( 
            "SELECT city_selected,movie_selected,theatre_selected,date_selected,number_of_tickets,seats_selected FROM User__Log where bank is not null and Username=? and date_selected>?", 
            (del_usname,del_now)) 
            quer = cur.fetchall() 
            if quer is not None: 
                li = list(quer) 
                print(li)
                deleted_items = [] 
                for i in li: 
                    item  = list(i) 
                    deleted_items.append(item) 
                return render_template('cancellation.html',deleted_items=deleted_items) 
            elif quer is None: 
                return "<center><h1>You have not booked any tickets</h1></center>" 
        elif query_del is None: 
            return "<center><h1>You have not signed up<a href='http://127.0.0.1:5000/signup'>Click here to Sign Up</a></h1></center>" 
    return render_template('cancellationlogin.html') 
 
#cancellation process 
@app.route('/cancellation',methods=['POST', 'GET']) 
def cancellation(): 
    if request.method == 'POST': 
        del_items = str(request.form.getlist("deleted_items")) 
        conn = get_db() 
        cur= conn.cursor() 
        x = del_items[2:-2]   
        y = x.split("', '") 
        for i in y: 
            z = i.split("|") 
            cur.execute("DELETE FROM User__log where city_selected = ? and movie_selected = ? and theatre_selected = ? and date_selected= ? and seats_selected = ?" 
            ,(z[0],z[1],z[2],z[3],z[5])) 
            conn.commit() 
            date = z[3][:10] 
            days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'] 
            day = datetime.datetime.strptime(date, '%Y-%m-%d').weekday() 
            delete_daytable = days[day] 
            a = f"SELECT Seats FROM {delete_daytable} WHERE Theatre = ? and date= ? AND Movie = ?" 
            print(a)
            cur.execute(a,(z[2],date,z[1]))
            query = cur.fetchall()
            seatnum = int(query[0][0]) if query else 0
            seats = str(seatnum + int(z[4]))
            query = f"UPDATE {delete_daytable} SET Seats = ? WHERE Theatre = ? and date= ? AND Movie = ?"
            print(query)
            cur.execute(query,(seats,z[2],date,z[1]))
            conn.commit() 
            cur.execute("DELETE FROM Seats WHERE Movie = ? and Theatre = ? and Date = ? and seats_selected = ?",(z[1],z[2],z[3],z[5])) 
            conn.commit() 
            a = list(query_del) 
            del_email = a[4] 
            message = Message( 
            'Ticket Cancellation', sender='ticketbox4567@gmail.com', recipients=[del_email]) 
            message.html = "<h1>Your tickets for " + z[1] + " at " + z[2] + " on " + z[3] + " for seats " + z[5] + " have been cancelled.</h1>" 
            mail.send(message) 
        return render_template('cancellationend.html') 
    return render_template('cancellation.html') 
 
# OTP verification(customers) 
@app.route('/verification', methods=['POST', 'GET']) 
def validate(): 
    if request.method == "POST": 
        user_otp = request.form['otp'] 
        if otp == int(user_otp): 
            return render_template('login.html') 
        else: 
            return "<center><h1>Your OTP is invalid<br><a href='http://127.0.0.1:5000/login'>Back to Login</a></h1></center>" 
    return render_template('verification.html') 
 
# login page render 
@app.route('/login', methods=['POST', 'GET']) 
def login(): 
    # 每次进入登录销毁管理员会话
    session.pop("is_admin", None)
    session.pop("admin_name", None)
    mode = request.args.get("mode")
    if request.method == "POST": 
        global usname 
        usname = request.form['username'] 
        passwd = request.form['password'] 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute( 
            "SELECT * FROM Administrator WHERE admin_name = ? AND admin_password = ?", (usname, passwd)) 
        account = cur.fetchone() 
        if account is None: 
            cur.execute( 
                'SELECT * FROM user WHERE username = ? AND password = ?', (usname, passwd)) 
            acc = cur.fetchone() 
            if acc is None: 
                return "<center><h1>Your username or password is invalid<br><a href='http://127.0.0.1:5000/login'>Back to Login</a></h1></center>" 
            else: 
                global now 
                now = time.strftime('%Y-%m-%d %H:%M:%S') 
                cur.execute( 
                    "INSERT into User__Log (Username, Login_time) VALUES (?, ?)", (usname, now)) 
                conn.commit() 
                cur.close() 
            return redirect('http://127.0.0.1:5000/cities', code=302) 
        else: 
            lt = time.strftime('%Y-%m-%d %H:%M:%S') 
            cur.execute( 
                "INSERT into Admin__Login (admin_name, login_time) VALUES (?, ?)", (usname, lt)) 
            conn.commit() 
            cur.close() 
            session["is_admin"] = True 
            session["admin_name"] = usname 
            return redirect('http://127.0.0.1:5000/admin/', code=302) 
    if not mode:
        return render_template('login_choice.html')
    return render_template('login.html', mode=mode) 
 
# admin verification 
@app.route('/adminverification', methods=['POST', 'GET']) 
def adminvalidate(): 
    if request.method == "POST": 
        user_otp = request.form['otpad'] 
        if otp1 == int(user_otp): 
            return redirect('http://127.0.0.1:5000/admin/', code=302) 
        else: 
            return "<center><h1>Your OTP is invalid<br><a href='http://127.0.0.1:5000/login'>Back to Login</a></h1></center>" 
    return render_template('adminverification.html') 
 
#city and movies page render 
@app.route('/cities', methods=['GET', 'POST']) 
def cities(): 
    if request.method == "POST": 
        global city 
        city = request.form["city"] 
        global city_id 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute("SELECT id FROM city WHERE name = ?", (city,)) 
        row_city = cur.fetchone() 
        city_id = row_city[0] if row_city else None 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute("UPDATE User__Log SET city_selected = ? WHERE Login_time = ?",(city,now)) 
        conn.commit() 
        # 优先从 schedule/movies 取丰富信息（rating、poster、summary），无数据再回退旧表
        cur.execute("""SELECT DISTINCT s.movie_id 
                       FROM schedule s 
                       JOIN theatre t ON s.theatre_id = t.id 
                       WHERE t.city_id = ?""", (city_id,)) 
        movie_ids = [r[0] for r in cur.fetchall()] 
        movies_info = [] 
        if movie_ids: 
            placeholders = ",".join(["?"] * len(movie_ids)) 
            cur.execute(f"SELECT id, title, rating, poster_path, summary FROM movies WHERE id IN ({placeholders})", movie_ids) 
            rows = cur.fetchall() 
            for mid, title, rating, poster, summary in rows: 
                movies_info.append({ 
                    "id": mid, 
                    "title": title, 
                    "rating": rating, 
                    "poster_path": poster, 
                    "summary": summary 
                }) 
        else: 
            cur.execute("SELECT Movies FROM Cities where City = ?", (city,)) 
            row = cur.fetchone() 
            mov_str = row[0] if row else "" 
            titles = [m.strip() for m in mov_str.split(",") if m.strip()] 
            for title in titles: 
                movies_info.append({ 
                    "id": None, 
                    "title": title, 
                    "rating": None, 
                    "poster_path": None, 
                    "summary": "" 
                }) 
        return render_template('movies.html', mov=movies_info, city=city) 
    elif request.method == "GET": 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute("""SELECT DISTINCT c.name 
                       FROM schedule s 
                       JOIN theatre t ON s.theatre_id = t.id 
                       JOIN city c ON c.id = t.city_id""") 
        data = cur.fetchall() 
        li = [r[0] for r in data] 
        if not li: 
            cur.execute("SELECT City FROM Cities") 
            data = cur.fetchall() 
            li = [x[0] for x in data] 
    return render_template('cities.html', name=usname, li=li) 
 
#movie updation in user_log table 
@app.route('/movies', methods=['GET','POST']) 
def movie(): 
    if request.method == "POST": 
        global movies 
        movies = request.form['movie'] 
        global movie_id 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute("SELECT id FROM movies WHERE title = ?", (movies,)) 
        row = cur.fetchone() 
        movie_id = row[0] if row else None 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute("UPDATE User__Log SET movie_selected = ? WHERE Login_time = ?",(movies,now)) 
        conn.commit() 
    return redirect('http://127.0.0.1:5000/theatres', code=302) 
 
#theatres and timing page render 
@app.route('/theatres', methods=['POST','GET']) 
def theatres(): 
    if request.method == "POST": 
        global theatre 
        theatre = request.form["theatre"] 
        global theatre_id 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute("UPDATE User__Log SET theatre_selected = ? WHERE Login_time = ?",(theatre,now)) 
        conn.commit() 
        cur.execute("SELECT id FROM theatre WHERE name = ? AND city_id = ?", (theatre, city_id)) 
        row = cur.fetchone() 
        theatre_id = row[0] if row else None 
        
        
        times = [] 
        return render_template('timings.html', times=times, movie=movies, theatre=theatre) 
    elif request.method == "GET": 
        conn = get_db() 
        cur = conn.cursor() 
        if not city_id: 
            return "<center><h1>Please select a city first</h1></center>" 
        cur.execute("""SELECT DISTINCT t.name 
                       FROM schedule s 
                       JOIN theatre t ON s.theatre_id = t.id 
                       WHERE t.city_id = ? AND s.movie_id = ?""",(city_id, movie_id)) 
        rows = cur.fetchall() 
        th = [r[0] for r in rows] 
        
    return render_template('theatres.html', th=th, movies=movies) 
 
#date to day conversion 
@app.route('/timings', methods=['POST', 'GET']) 
def timings(): 
    if request.method == 'POST': 
        global date
        date = request.form["dateselected"] 
        print(date)
        print(datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%A"))
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute("UPDATE User__Log SET date_selected = ? WHERE Login_time = ?",(date,now)) 
        conn.commit() 
        # 确定 schedule 是否存在
        global schedule_id
        cur.execute("SELECT id, available_seats FROM schedule WHERE movie_id = ? AND theatre_id = ? AND show_date = ?", (movie_id, theatre_id, date))
        row = cur.fetchone()
        if row:
            schedule_id = row[0]
        else:
            schedule_id = None
    return redirect('http://127.0.0.1:5000/seatavailability', code=302) 
 
# display number of seats and entering number of seats 
@app.route('/seatavailability', methods=['POST', 'GET']) 
def seatavailability(): 
    global schedule_id 
    if request.method == "POST": 
        global seat 
        seat = int(request.form["seats"]) 
        conn = get_db() 
        cur = conn.cursor() 
        if schedule_id is None: 
            # 创建新的排期，默认总座位 60
            cur.execute("INSERT INTO schedule (movie_id, theatre_id, show_date, total_seats, available_seats) VALUES (?, ?, ?, ?, ?)", 
                        (movie_id, theatre_id, date, 60, 60)) 
            schedule_id = cur.lastrowid 
            conn.commit() 
        cur.execute("SELECT available_seats FROM schedule WHERE id = ?", (schedule_id,)) 
        row = cur.fetchone() 
        seatnum = int(row[0]) if row else 0 
        global seats_in
        seats_in = seatnum - seat 
        
        return redirect('http://127.0.0.1:5000/booked', code=302) 
    elif request.method == 'GET': 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute("SELECT id, available_seats FROM schedule WHERE movie_id = ? AND theatre_id = ? AND show_date = ?", (movie_id, theatre_id, date)) 
        row = cur.fetchone() 
        if row is None: 
            seatnum = "60" 
            cur.execute("INSERT INTO schedule (movie_id, theatre_id, show_date, total_seats, available_seats) VALUES (?, ?, ?, ?, ?)", 
                        (movie_id, theatre_id, date, 60, 60)) 
            schedule_id = cur.lastrowid 
            conn.commit() 
        else: 
            schedule_id = row[0] 
            seatnum = str(row[1])  
        global newdate 
        newdate = date 
        cur.execute("UPDATE User__Log SET date_selected = ? WHERE Login_time = ?",(newdate,now)) 
        conn.commit() 
    return render_template('seatavailability.html',date=newdate,theatre=theatre,seatnum = seatnum,movies=movies) 
 
#choosing seats 
@app.route('/booked', methods=['POST', 'GET']) 
def booked(): 
    if request.method == 'POST': 
        seats = request.form.getlist("seat_selected") 
        global seatslist 
        seatslist = "" 
        amount=0 
        if len(seats) != seat: 
            return "<center><h1>请按照正确的数量选择座位！<br><a href='http://127.0.0.1:5000/booked'>返回重新选择</a></h1></center>" 
        for i in seats: 
            seatslist = seatslist+i+',' 
            if i[0] in ['A', 'B', 'C', 'D', 'E', 'F','G']: 
                amount+=180 
            else: 
                amount+=120 
        global amount_pay 
        amount_pay = amount 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute("UPDATE User__Log SET amount_paid = ? , seats_selected = ? WHERE Login_time = ?",(amount,seatslist,now)) 
        cur.execute("UPDATE User__Log SET number_of_tickets = ? WHERE Login_time = ?",(str(seat),now))  
        conn.commit() 
        return render_template('payment.html',amount=amount) 
    elif request.method == 'GET': 
        conn = get_db() 
        cur= conn.cursor() 
        cur.execute("SELECT seat_code from seat_booking WHERE schedule_id = ?", (schedule_id,)) 
        rows = cur.fetchall() 
        selected = [r[0] for r in rows] 
    return render_template('seats.html', selected=selected, seat=seat) 
 
#payment page 
@app.route('/payment', methods=['GET', 'POST']) 
def payment(): 
    if request.method == "POST": 
        details = request.form 
        banks = details['banks'] 
        cards = details['cards'] 
        cardno = details['cardno'] 
        expdate = details['expdate'] 
        cvvno = '' 
        name = details['name_card'] 
        conn = get_db() 
        cur = conn.cursor() 
        cur.execute("SELECT * from User where username = ?",(usname,)) 
        query = cur.fetchone() 
        a = list(query) 
        global user_email 
        user_email = a[4] 
        global pay_otp 
        pay_otp = randint(000000, 999999) 
        cur.execute("UPDATE User__Log SET bank = ?, card_type = ?, card_number = ?,expiration_date = ?, cvv_number = ?, name_on_card = ? WHERE Login_time = ?",  
        (banks,cards,cardno,expdate,cvvno,name,now)) 
        conn.commit() 
        cur.close() 
        message = Message( 
            'Payment Verification code for TicketBox', sender='ticketbox4567@gmail.com', recipients=[user_email]) 
        message.body = "Your 6-digit OTP code is " + str(pay_otp) 
        send_mail_safely(message) 
        return redirect("http://127.0.0.1:5000/otp") 
    return render_template('payment.html') 
 
#otp verification for payment 
@app.route('/otp', methods=['POST', 'GET']) 
def paymentverification(): 
    if request.method == "POST": 
        use_otp = request.form['payment_otp'] 
        if pay_otp == int(use_otp): 
            message = Message('Confirmation Mail',sender='ticketbox4567@gmail.com', recipients=[user_email]) 
            message.html = "<h1>Your ticket has been booked!<br> City: " + city +"<br> Theatre: " + theatre + "<br> Movie: " + movies + "<br> Timings: " + str(newdate) + "<br> Seats: " + seatslist + "</h1>" 
            send_mail_safely(message) 
            # 记录订单
            conn = get_db()
            cur = conn.cursor()
            # 获取 user_id
            cur.execute("SELECT id FROM user WHERE username = ?", (usname,))
            user_row = cur.fetchone()
            uid = user_row[0] if user_row else None
            # 插入座位占用
            for seat_code in seatslist.split(','):
                if seat_code:
                    cur.execute("INSERT INTO seat_booking (schedule_id, seat_code) VALUES (?, ?)", (schedule_id, seat_code))
            # 更新排期可用座位
            cur.execute("UPDATE schedule SET available_seats = ? WHERE id = ?", (seats_in, schedule_id))
            cur.execute("INSERT INTO orders (user_id, schedule_id, seat_count, amount, status) VALUES (?, ?, ?, ?, ?)",
                        (uid, schedule_id, seat, amount_pay, "paid"))
            conn.commit()
            return render_template('done.html') 
        else: 
            return "<center><h1>Your OTP is invalid<br><a href='http://127.0.0.1:5000/payment'>Back toPayment</a></h1></center>" 
    return render_template('otp.html') 
 
if __name__ == '__main__': 
    app.run(debug=True)
