from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import sqlite3
import os
from datetime import date, datetime
from functools import wraps
from werkzeug.security import check_password_hash
from dotenv import load_dotenv
import razorpay

load_dotenv()

DATABASE = os.path.join(os.path.dirname(__file__), "TrekManagement.db")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY", "trekker_secret_key_default")

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")
RAZORPAY_CURRENCY = os.environ.get("RAZORPAY_CURRENCY", "INR")
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)) if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET else None

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

@app.teardown_appcontext
def close_db(_exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS User (
        UserId INTEGER PRIMARY KEY AUTOINCREMENT,
        FullName TEXT,
        UserEmail TEXT UNIQUE,
        UserPassword TEXT,
        UserRole TEXT,
        Contact TEXT
    );""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Trek (
        TrekId INTEGER PRIMARY KEY AUTOINCREMENT,
        TrekName TEXT NOT NULL,
        Difficulty TEXT,
        Location TEXT,
        Duration_HRS INTEGER,
        StartDate DATE,
        EndDate DATE,
        Slot INTEGER,
        StaffId INTEGER,
        Status TEXT,
        Participants INTEGER DEFAULT 0,
        Price INTEGER DEFAULT 1500,
        FOREIGN KEY(StaffId) REFERENCES User(UserId) ON DELETE SET NULL
    );""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Booking (
        BookingId INTEGER PRIMARY KEY AUTOINCREMENT,
        UserId INTEGER, 
        TrekId INTEGER,
        BookingStatus TEXT,
        BookingDate DATE,
        PaymentStatus TEXT,
        RazorpayOrderId TEXT,
        RazorpayPaymentId TEXT,
        FOREIGN KEY(UserId) REFERENCES User(UserId) ON DELETE CASCADE,
        FOREIGN KEY(TrekId) REFERENCES Trek(TrekId) ON DELETE CASCADE
    );""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS StaffReq (
        ReqId INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Email TEXT,
        Password TEXT,
        Contact TEXT
    );""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS History (
        BookingId INTEGER,
        TrekkerId INTEGER,
        TrekkerName TEXT,
        TrekId INTEGER,
        TrekName TEXT,
        StaffId INTEGER,
        StaffName TEXT,
        TrekStart DATE,
        TrekEnd DATE,
        BookingDate DATE,
        Status TEXT
    );""")

    cursor.execute("PRAGMA table_info(Trek)")
    trek_cols = [col[1] for col in cursor.fetchall()]
    if 'Price' not in trek_cols:
        cursor.execute("ALTER TABLE Trek ADD COLUMN Price INTEGER DEFAULT 1500;")

    cursor.execute("PRAGMA table_info(Booking)")
    booking_cols = [col[1] for col in cursor.fetchall()]
    if 'RazorpayOrderId' not in booking_cols:
        cursor.execute("ALTER TABLE Booking ADD COLUMN RazorpayOrderId TEXT;")
    if 'RazorpayPaymentId' not in booking_cols:
        cursor.execute("ALTER TABLE Booking ADD COLUMN RazorpayPaymentId TEXT;")

    demo_users = [
        ("Gaurav", "aroraganesh2007@gmail.com", "Admin", "9999999999"),
        ("Sample Trekker", "trekker@example.com", "Trekker", "9999999998"),
        ("Sample Staff", "staff@example.com", "Staff", "9999999997"),
    ]
    demo_password = "15022026"
    for full_name, email, role, contact in demo_users:
        cursor.execute("SELECT UserId, UserPassword FROM User WHERE UserEmail=?", (email,))
        existing_user = cursor.fetchone()
        if existing_user is None:
            cursor.execute("INSERT INTO User (FullName, UserEmail, UserPassword, UserRole, Contact) VALUES (?, ?, ?, ?, ?)",
                           (full_name, email, demo_password, role, contact))
        else:
            # If demo user still has an old hash, update to plain text
            pwd = existing_user[1]
            if pwd and (pwd.startswith("scrypt:") or pwd.startswith("pbkdf2:")):
                cursor.execute("UPDATE User SET UserPassword=? WHERE UserId=?", (demo_password, existing_user[0]))

    conn.commit()
    conn.close()

init_db()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "UserId" not in session:
            flash("Please login first to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if session.get("Role") != role:
                flash("You do not have permission to access this resource.", "error")
                return render_template("unauthorized.html"), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/', methods=["GET", "POST"])
def index():
    if "UserId" in session:
        role = session.get("Role")
        if role == "Admin":
            return redirect(url_for("adminDashboard"))
        elif role == "Staff":
            return redirect(url_for("staffDashboard"))
        elif role == "Trekker":
            return redirect(url_for("trekkerDashboard"))
    return redirect(url_for("login"))


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("Username", "").strip()
        password = request.form.get("Password", "").strip()

        if not username or not password:
            flash("All fields are required", "warning")
            return redirect(url_for("login"))

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM User WHERE UserEmail=?", (username,))
        user = cursor.fetchone()

        if user:
            stored_password = user["UserPassword"]
            is_valid = False
            if stored_password == password:
                is_valid = True
            elif stored_password and (stored_password.startswith("scrypt:") or stored_password.startswith("pbkdf2:")):
                # Migrate any legacy hash to plain text upon successful verification
                if check_password_hash(stored_password, password):
                    is_valid = True
                    cursor.execute("UPDATE User SET UserPassword=? WHERE UserId=?", (password, user["UserId"]))
                    db.commit()

            if is_valid:
                session['UserId'] = user["UserId"]
                session['Role'] = user["UserRole"]
                session['FullName'] = user["FullName"]
                flash(f"Welcome back, {user['FullName']}!", "success")

                if user["UserRole"] == "Admin":
                    return redirect(url_for("adminDashboard"))
                elif user["UserRole"] == "Staff":
                    return redirect(url_for("staffDashboard"))
                else:
                    return redirect(url_for("trekkerDashboard"))

        flash("Invalid email or password", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("Fullname", "").strip()
        email = request.form.get("Email", "").strip()
        password = request.form.get("Password", "").strip()
        password2 = request.form.get("Password2", "").strip()
        contact = request.form.get("Contact", "").strip()
        role = request.form.get("Role", "").strip()

        if not name or not password or not password2 or not email or not contact or not role:
            flash("All fields are required", "warning")
            return redirect(url_for("register"))

        if password != password2:
            flash("Passwords do not match", "error")
            return redirect(url_for("register"))

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT UserEmail FROM User WHERE UserEmail=?", (email,))
        if cursor.fetchone():
            flash("Email is already registered. Please login.", "error")
            return redirect(url_for("register"))

        cursor.execute("SELECT Email FROM StaffReq WHERE Email=?", (email,))
        if cursor.fetchone():
            flash("You have already submitted a staff request. Please wait for admin approval.", "warning")
            return redirect(url_for("register"))

        if role == "Trekker":
            cursor.execute("INSERT INTO User (FullName, UserEmail, UserPassword, UserRole, Contact) VALUES (?, ?, ?, 'Trekker', ?)",
                           (name, email, password, contact))
            db.commit()
            flash("Successfully registered as Trekker! You can now login.", "success")
            return redirect(url_for("login"))
        elif role == "Staff":
            cursor.execute("INSERT INTO StaffReq (Name, Email, Password, Contact) VALUES (?, ?, ?, ?)",
                           (name, email, password, contact))
            db.commit()
            flash("Staff approval request sent to Admin. You can login once approved.", "success")
            return redirect(url_for("login"))
        else:
            flash("Invalid role selected.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("login"))


@app.route('/adminDashboard')
@role_required("Admin")
def adminDashboard():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT count(TrekId) FROM Trek")
    total_treks = cursor.fetchone()[0]

    cursor.execute("SELECT count(UserId) FROM User WHERE UserRole='Trekker'")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT count(UserId) FROM User WHERE UserRole='Staff'")
    total_staff = cursor.fetchone()[0]

    cursor.execute("SELECT count(BookingId) FROM Booking")
    total_bookings = cursor.fetchone()[0]

    cursor.execute("""SELECT b.BookingId, u.FullName, t.TrekName, b.BookingStatus, b.BookingDate 
                      FROM Booking b 
                      JOIN Trek t ON b.TrekId=t.TrekId 
                      JOIN User u ON b.UserId=u.UserId 
                      ORDER BY b.BookingDate DESC LIMIT 5""")
    recent_bookings = cursor.fetchall()

    cursor.execute("SELECT * FROM User WHERE UserId=?", (session.get("UserId"),))
    user_info = cursor.fetchone()

    return render_template("adminDashboard.html",
                           TotalTreks=total_treks,
                           TotalUsers=total_users,
                           TotalStaff=total_staff,
                           TotalBookings=total_bookings,
                           bookings=recent_bookings,
                           UserInfo=user_info)


@app.route('/addTrek', methods=["GET", "POST"])
@role_required("Admin")
def addTrek():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        name = request.form.get("Trekname", "").strip()
        difficulty = request.form.get("Difficulty", "").strip()
        location = request.form.get("Location", "").strip()
        duration = request.form.get("Duration", "").strip()
        s_date = request.form.get("sDate", "").strip()
        e_date = request.form.get("eDate", "").strip()
        slot = request.form.get("Slot", "").strip()
        price = request.form.get("Price", "1500").strip()
        staff_id = request.form.get("StaffId", "").strip()

        if not name or not difficulty or not location or not duration or not s_date or not e_date or not slot:
            flash("All required fields must be filled", "warning")
            return redirect(url_for("addTrek"))

        try:
            duration = int(duration)
            slot = int(slot)
            price = int(price)
        except ValueError:
            flash("Duration, slots, and price must be numbers.", "error")
            return redirect(url_for("addTrek"))

        if duration <= 0 or slot <= 0 or price <= 0:
            flash("Duration, slots, and price must be greater than zero.", "error")
            return redirect(url_for("addTrek"))

        if e_date < s_date:
            flash("End date cannot be earlier than start date.", "error")
            return redirect(url_for("addTrek"))

        staff_val = int(staff_id) if staff_id else None
        if staff_val:
            cursor.execute("SELECT UserId FROM User WHERE UserId=? AND UserRole='Staff'", (staff_val,))
            if not cursor.fetchone():
                flash("Selected staff member does not exist.", "error")
                return redirect(url_for("addTrek"))

        cursor.execute("""INSERT INTO Trek (TrekName, Difficulty, Location, Duration_HRS, StartDate, EndDate, Slot, StaffId, Status, Price) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?)""",
                       (name, difficulty, location, duration, s_date, e_date, slot, staff_val, price))
        db.commit()
        flash("New Trek created successfully!", "success")
        return redirect(url_for("adminTreks"))

    cursor.execute("SELECT UserId, Fullname FROM User WHERE UserRole='Staff'")
    staffs = cursor.fetchall()
    return render_template("addTrek.html", staffs=staffs)


@app.route("/adminTreks", methods=["GET", "POST"])
@role_required("Admin")
def adminTreks():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        search_query = request.form.get("NameorId", "").strip()
        if search_query:
            try:
                val = int(search_query)
                return redirect(url_for("searchTrek", x=val, y=0))
            except ValueError:
                return redirect(url_for("searchTrek", x=search_query, y=1))
        else:
            flash("Please enter a search value", "warning")
            return redirect(url_for("adminTreks"))

    cursor.execute("SELECT t.*, s.FullName as StaffName FROM Trek t LEFT JOIN User s ON t.StaffId=s.UserId")
    treks = cursor.fetchall()
    return render_template("adminTreks.html", treks=treks)


@app.route("/editTrek/<int:TrekId>", methods=["GET", "POST"])
@role_required("Admin")
def editTrek(TrekId):
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        name = request.form.get("Trekname", "").strip()
        difficulty = request.form.get("Difficulty", "").strip()
        location = request.form.get("Location", "").strip()
        duration = request.form.get("Duration", "").strip()
        s_date = request.form.get("sDate", "").strip()
        e_date = request.form.get("eDate", "").strip()
        slot = request.form.get("Slot", "").strip()
        price = request.form.get("Price", "1500").strip()
        staff_id = request.form.get("StaffId", "").strip()
        status = request.form.get("Status", "Open").strip()

        if not name or not difficulty or not location or not duration or not s_date or not e_date or not slot:
            flash("All fields are required.", "warning")
            return redirect(url_for("editTrek", TrekId=TrekId))

        try:
            duration = int(duration)
            slot = int(slot)
            price = int(price)
        except ValueError:
            flash("Duration, slots, and price must be numbers.", "error")
            return redirect(url_for("editTrek", TrekId=TrekId))

        if duration <= 0 or slot <= 0 or price <= 0:
            flash("Values must be greater than 0.", "error")
            return redirect(url_for("editTrek", TrekId=TrekId))

        if e_date < s_date:
            flash("End date cannot be earlier than start date.", "error")
            return redirect(url_for("editTrek", TrekId=TrekId))

        cursor.execute("SELECT Participants FROM Trek WHERE TrekId=?", (TrekId,))
        trek_row = cursor.fetchone()
        if not trek_row:
            flash("Trek not found.", "error")
            return redirect(url_for("adminTreks"))

        if slot < trek_row["Participants"]:
            flash("Total slots cannot be less than existing bookings count.", "error")
            return redirect(url_for("editTrek", TrekId=TrekId))

        staff_val = int(staff_id) if staff_id else None

        cursor.execute("""UPDATE Trek SET TrekName=?, Difficulty=?, Location=?, Duration_HRS=?, StartDate=?, EndDate=?, Slot=?, StaffId=?, Status=?, Price=? WHERE TrekId=?""",
                       (name, difficulty, location, duration, s_date, e_date, slot, staff_val, status, price, TrekId))
        db.commit()
        flash("Trek updated successfully!", "success")
        return redirect(url_for("adminTreks"))

    cursor.execute("SELECT * FROM Trek WHERE TrekId=?", (TrekId,))
    trek = cursor.fetchone()
    if not trek:
        return "Trek not found", 404

    cursor.execute("SELECT UserId, Fullname FROM User WHERE UserRole='Staff'")
    staffs = cursor.fetchall()
    return render_template("editTrek.html", trek=trek, staffs=staffs, staffId=trek["StaffId"])


@app.route("/removeTrek/<int:TrekId>")
@role_required("Admin")
def removeTrek(TrekId):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT BookingId FROM Booking WHERE TrekId=?", (TrekId,))
    bookings = cursor.fetchall()

    for b in bookings:
        b_id = b["BookingId"]
        cursor.execute("""SELECT b.BookingId, u.UserId, u.FullName, t.TrekId, t.TrekName, t.StaffId, s.FullName, t.StartDate, t.EndDate, b.BookingDate, 'Revoked'
                          FROM Booking b 
                          JOIN Trek t ON b.TrekId=t.TrekId 
                          JOIN User u ON b.UserId=u.UserId 
                          LEFT JOIN User s ON t.StaffId=s.UserId 
                          WHERE b.BookingId=?""", (b_id,))
        data = cursor.fetchone()
        if data:
            cursor.execute("INSERT INTO History VALUES (?,?,?,?,?,?,?,?,?,?,?)", tuple(data))

    cursor.execute("DELETE FROM Trek WHERE TrekId=?", (TrekId,))
    db.commit()
    flash("Trek removed and active bookings logged into history.", "success")
    return redirect(url_for("adminTreks"))


@app.route("/searchTrek/<x>/<int:y>", methods=["GET", "POST"])
@role_required("Admin")
def searchTrek(x, y):
    db = get_db()
    cursor = db.cursor()
    if y == 1:
        cursor.execute("SELECT t.*, s.FullName as StaffName FROM Trek t LEFT JOIN User s ON t.StaffId=s.UserId WHERE t.TrekName LIKE ?", (f"%{x}%",))
    else:
        cursor.execute("SELECT t.*, s.FullName as StaffName FROM Trek t LEFT JOIN User s ON t.StaffId=s.UserId WHERE t.TrekId=?", (x,))
    treks = cursor.fetchall()
    return render_template("adminTreks.html", treks=treks)


@app.route("/adminTrekkers", methods=["GET", "POST"])
@role_required("Admin")
def adminTrekkers():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        search_val = request.form.get("NameorId", "").strip()
        if search_val:
            try:
                val = int(search_val)
                return redirect(url_for("searchTrekker", x=val, y=0))
            except ValueError:
                return redirect(url_for("searchTrekker", x=search_val, y=1))
        else:
            flash("Please enter search text", "warning")
            return redirect(url_for("adminTrekkers"))

    cursor.execute("SELECT * FROM User WHERE UserRole='Trekker'")
    users = cursor.fetchall()
    return render_template("adminTrekkers.html", users=users)


@app.route("/searchUser/<x>/<int:y>", methods=["GET", "POST"])
@role_required("Admin")
def searchTrekker(x, y):
    db = get_db()
    cursor = db.cursor()
    if y == 1:
        cursor.execute("SELECT * FROM User WHERE FullName LIKE ? AND UserRole='Trekker'", (f"%{x}%",))
    else:
        cursor.execute("SELECT * FROM User WHERE UserId=? AND UserRole='Trekker'", (x,))
    users = cursor.fetchall()
    return render_template("adminTrekkers.html", users=users)


@app.route("/blacklist/<int:UserId>")
@role_required("Admin")
def blacklist(UserId):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT TrekId FROM Booking WHERE UserId=?", (UserId,))
    user_bookings = cursor.fetchall()

    for b in user_bookings:
        cursor.execute("UPDATE Trek SET Participants = MAX(0, Participants - 1) WHERE TrekId=?", (b["TrekId"],))

    cursor.execute("DELETE FROM User WHERE UserId=? AND UserRole='Trekker'", (UserId,))
    db.commit()
    flash("Trekker blacklisted and deleted successfully.", "success")
    return redirect(url_for("adminTrekkers"))


@app.route("/adminStaff", methods=["GET", "POST"])
@role_required("Admin")
def adminStaff():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        search_val = request.form.get("NameorId", "").strip()
        if search_val:
            try:
                val = int(search_val)
                return redirect(url_for("searchStaff", x=val, y=0))
            except ValueError:
                return redirect(url_for("searchStaff", x=search_val, y=1))
        else:
            flash("Please enter search criteria", "warning")
            return redirect(url_for("adminStaff"))

    cursor.execute("SELECT * FROM User WHERE UserRole='Staff'")
    staffs = cursor.fetchall()
    cursor.execute("SELECT * FROM StaffReq")
    reqstaffs = cursor.fetchall()
    return render_template("adminStaff.html", staffs=staffs, reqstaffs=reqstaffs)


@app.route("/searchStaff/<x>/<int:y>", methods=["GET", "POST"])
@role_required("Admin")
def searchStaff(x, y):
    db = get_db()
    cursor = db.cursor()
    if y == 1:
        cursor.execute("SELECT * FROM User WHERE FullName LIKE ? AND UserRole='Staff'", (f"%{x}%",))
    else:
        cursor.execute("SELECT * FROM User WHERE UserId=? AND UserRole='Staff'", (x,))
    staffs = cursor.fetchall()
    cursor.execute("SELECT * FROM StaffReq")
    reqstaffs = cursor.fetchall()
    return render_template("adminStaff.html", staffs=staffs, reqstaffs=reqstaffs)


@app.route("/blacklistS/<int:UserId>")
@role_required("Admin")
def blacklistS(UserId):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT t.TrekId FROM Trek t JOIN Booking b ON t.TrekId=b.TrekId WHERE t.StaffId=?", (UserId,))
    assigned_treks = cursor.fetchall()

    if assigned_treks:
        return redirect(url_for("replaceStaff", StaffId=UserId))

    cursor.execute("UPDATE Trek SET StaffId=NULL WHERE StaffId=?", (UserId,))
    cursor.execute("DELETE FROM User WHERE UserId=? AND UserRole='Staff'", (UserId,))
    db.commit()
    flash("Staff member deleted.", "success")
    return redirect(url_for("adminStaff"))


@app.route("/replaceStaff/<int:StaffId>", methods=["GET", "POST"])
@role_required("Admin")
def replaceStaff(StaffId):
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        cursor.execute("SELECT DISTINCT t.TrekId FROM Trek t JOIN Booking b ON t.TrekId=b.TrekId WHERE t.StaffId=?", (StaffId,))
        treks = cursor.fetchall()
        count = 1
        for trek in treks:
            new_staff_id = request.form.get(f"StaffId{count}")
            count += 1
            if new_staff_id:
                cursor.execute("SELECT UserId FROM User WHERE UserId=? AND UserRole='Staff'", (new_staff_id,))
                if cursor.fetchone():
                    cursor.execute("UPDATE Trek SET StaffId=? WHERE TrekId=?", (new_staff_id, trek["TrekId"]))

        cursor.execute("DELETE FROM User WHERE UserId=? AND UserRole='Staff'", (StaffId,))
        db.commit()
        flash("Staff reassigned and former staff deleted successfully.", "success")
        return redirect(url_for("adminStaff"))

    cursor.execute("SELECT UserId, Fullname FROM User WHERE UserRole='Staff' AND UserId!=?", (StaffId,))
    staffs = cursor.fetchall()
    cursor.execute("SELECT DISTINCT t.TrekId, t.TrekName FROM Trek t JOIN Booking b ON t.TrekId=b.TrekId WHERE t.StaffId=?", (StaffId,))
    treks = cursor.fetchall()
    flash("The staff member has active assigned treks with bookings. Reassign them below.", "warning")
    return render_template("replaceStaff.html", treks=treks, staffs=staffs, sId=StaffId)


@app.route("/approve/<int:ReqId>", methods=["GET", "POST"])
@role_required("Admin")
def approve(ReqId):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM StaffReq WHERE ReqId=?", (ReqId,))
    staff = cursor.fetchone()
    if staff:
        cursor.execute("INSERT INTO User (FullName, UserEmail, UserPassword, UserRole, Contact) VALUES (?, ?, ?, 'Staff', ?)",
                       (staff["Name"], staff["Email"], staff["Password"], staff["Contact"]))
        cursor.execute("DELETE FROM StaffReq WHERE ReqId=?", (ReqId,))
        db.commit()
        flash(f"Staff request for {staff['Name']} approved!", "success")
    return redirect(url_for("adminStaff"))


@app.route("/reject/<int:ReqId>", methods=["GET", "POST"])
@role_required("Admin")
def reject(ReqId):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM StaffReq WHERE ReqId=?", (ReqId,))
    db.commit()
    flash("Staff request rejected.", "info")
    return redirect(url_for("adminStaff"))


@app.route("/adminBookings", methods=["GET", "POST"])
@role_required("Admin")
def adminBooking():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        name_or_id = request.form.get("NameorId", "").strip()
        search_by = request.form.get("SearchBy", "").strip()
        if name_or_id:
            try:
                val = int(name_or_id)
                return redirect(url_for("searchBooking", x=val, y=0, s=search_by))
            except ValueError:
                return redirect(url_for("searchBooking", x=name_or_id, y=1, s=search_by))
        else:
            flash("Please enter search keyword.", "warning")
            return redirect(url_for("adminBooking"))

    cursor.execute("""SELECT b.BookingId, b.TrekId, t.TrekName, s.UserId as StaffId, s.FullName as StaffName, u.UserId as TrekkerId, u.FullName as TrekkerName, b.BookingStatus, b.PaymentStatus 
                      FROM Booking b
                      JOIN Trek t ON b.TrekId=t.TrekId 
                      JOIN User u ON b.UserId=u.UserId 
                      LEFT JOIN User s ON t.StaffId=s.UserId 
                      ORDER BY b.BookingStatus""")
    bookings = cursor.fetchall()
    return render_template("adminBookings.html", bookings=bookings)


@app.route("/searchBooking/<x>/<int:y>/<string:s>", methods=["GET", "POST"])
@role_required("Admin")
def searchBooking(x, y, s):
    db = get_db()
    cursor = db.cursor()
    base_query = """SELECT b.BookingId, b.TrekId, t.TrekName, s.UserId as StaffId, s.FullName as StaffName, u.UserId as TrekkerId, u.FullName as TrekkerName, b.BookingStatus, b.PaymentStatus 
                    FROM Booking b
                    JOIN Trek t ON b.TrekId=t.TrekId 
                    JOIN User u ON b.UserId=u.UserId 
                    LEFT JOIN User s ON t.StaffId=s.UserId """

    if s == "BookingId":
        cursor.execute(base_query + "WHERE b.BookingId=? ORDER BY b.BookingStatus", (x,))
    elif s == "TrekIdorName":
        if y == 0:
            cursor.execute(base_query + "WHERE b.TrekId=? ORDER BY b.BookingStatus", (x,))
        else:
            cursor.execute(base_query + "WHERE t.TrekName LIKE ? ORDER BY b.BookingStatus", (f"%{x}%",))
    elif s == "StaffIdorName":
        if y == 0:
            cursor.execute(base_query + "WHERE s.UserId=? ORDER BY b.BookingStatus", (x,))
        else:
            cursor.execute(base_query + "WHERE s.FullName LIKE ? ORDER BY b.BookingStatus", (f"%{x}%",))
    elif s == "UserIdorName":
        if y == 0:
            cursor.execute(base_query + "WHERE u.UserId=? ORDER BY b.BookingStatus", (x,))
        else:
            cursor.execute(base_query + "WHERE u.FullName LIKE ? ORDER BY b.BookingStatus", (f"%{x}%",))
    else:
        cursor.execute(base_query + "ORDER BY b.BookingStatus")

    bookings = cursor.fetchall()
    return render_template("adminBookings.html", bookings=bookings)


@app.route("/adminHistory", methods=["GET", "POST"])
@role_required("Admin")
def adminHistory():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        search_val = request.form.get("NameorId", "").strip()
        search_by = request.form.get("SearchBy", "").strip()
        if search_val:
            try:
                val = int(search_val)
                return redirect(url_for("searchHistory", x=val, y=0, s=search_by))
            except ValueError:
                return redirect(url_for("searchHistory", x=search_val, y=1, s=search_by))
        else:
            flash("Please enter search keyword.", "warning")
            return redirect(url_for("adminHistory"))

    cursor.execute("SELECT * FROM History")
    trekkings = cursor.fetchall()
    return render_template("adminHistory.html", trekkings=trekkings)


@app.route("/searchHistory/<x>/<int:y>/<string:s>", methods=["GET", "POST"])
@role_required("Admin")
def searchHistory(x, y, s):
    db = get_db()
    cursor = db.cursor()
    if s == "BookingId":
        cursor.execute("SELECT * FROM History WHERE BookingId=?", (x,))
    elif s == "TrekIdorName":
        if y == 0:
            cursor.execute("SELECT * FROM History WHERE TrekId=?", (x,))
        else:
            cursor.execute("SELECT * FROM History WHERE TrekName LIKE ?", (f"%{x}%",))
    elif s == "StaffIdorName":
        if y == 0:
            cursor.execute("SELECT * FROM History WHERE StaffId=?", (x,))
        else:
            cursor.execute("SELECT * FROM History WHERE StaffName LIKE ?", (f"%{x}%",))
    elif s == "UserIdorName":
        if y == 0:
            cursor.execute("SELECT * FROM History WHERE TrekkerId=?", (x,))
        else:
            cursor.execute("SELECT * FROM History WHERE TrekkerName LIKE ?", (f"%{x}%",))
    else:
        cursor.execute("SELECT * FROM History")

    trekkings = cursor.fetchall()
    return render_template("adminHistory.html", trekkings=trekkings)


@app.route('/staffDashboard')
@role_required("Staff")
def staffDashboard():
    db = get_db()
    cursor = db.cursor()
    staff_id = session.get("UserId")

    cursor.execute("SELECT * FROM User WHERE UserId=?", (staff_id,))
    user_info = cursor.fetchone()

    cursor.execute("SELECT TrekId, TrekName, Location, Participants, Slot, Status FROM Trek WHERE StaffId=? LIMIT 3", (staff_id,))
    a_treks = cursor.fetchall()

    cursor.execute("SELECT count(TrekId) FROM Trek WHERE StaffId=?", (staff_id,))
    assigned_count = cursor.fetchone()[0]

    cursor.execute("""SELECT count(u.UserId) FROM Trek t 
                      JOIN Booking b ON t.TrekId=b.TrekId 
                      JOIN User u ON b.UserId=u.UserId 
                      WHERE t.StaffId=?""", (staff_id,))
    participant_count = cursor.fetchone()[0]

    cursor.execute("SELECT count(DISTINCT TrekId) FROM History WHERE StaffId=?", (staff_id,))
    completed_count = cursor.fetchone()[0]

    return render_template("staffDashboard.html",
                           UserInfo=user_info,
                           aTreks=a_treks,
                           a=assigned_count,
                           p=participant_count,
                           c=completed_count)


@app.route("/staffProfile")
@role_required("Staff")
def staffProfile():
    db = get_db()
    cursor = db.cursor()
    staff_id = session.get("UserId")
    cursor.execute("SELECT UserId, Fullname, UserEmail, Contact FROM User WHERE UserId=?", (staff_id,))
    staff = cursor.fetchone()
    cursor.execute("SELECT count(DISTINCT TrekId) FROM History WHERE StaffId=?", (staff_id,))
    c = cursor.fetchone()[0]
    return render_template("staffProfile.html", Staff=staff, c=c)


@app.route("/assignedTreks")
@role_required("Staff")
def assignedTreks():
    db = get_db()
    cursor = db.cursor()
    staff_id = session.get("UserId")
    cursor.execute("SELECT * FROM Trek WHERE StaffId=?", (staff_id,))
    a_treks = cursor.fetchall()
    return render_template("assignedTreks.html", aTreks=a_treks)


@app.route("/staffTrekkers")
@role_required("Staff")
def staffTrekkers():
    db = get_db()
    cursor = db.cursor()
    staff_id = session.get("UserId")

    cursor.execute("""SELECT t.TrekId, u.UserId, t.TrekName, u.FullName, u.UserEmail, u.Contact 
                      FROM Trek t 
                      JOIN Booking b ON t.TrekId=b.TrekId 
                      JOIN User u ON b.UserId=u.UserId 
                      WHERE t.StaffId=? AND b.BookingStatus='Booked'""", (staff_id,))
    trekkers = cursor.fetchall()

    cursor.execute("""SELECT DISTINCT t.TrekId, t.TrekName 
                      FROM Trek t 
                      JOIN Booking b ON t.TrekId=b.TrekId 
                      WHERE t.StaffId=? AND b.BookingStatus='Booked'""", (staff_id,))
    a_treks = cursor.fetchall()

    return render_template("staffTrekkers.html", aTreks=a_treks, Trekkers=trekkers)


@app.route("/editStaffProfile", methods=["GET", "POST"])
@role_required("Staff")
def editStaffProfile():
    db = get_db()
    cursor = db.cursor()
    staff_id = session.get("UserId")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        contact = request.form.get("contact", "").strip()

        cursor.execute("SELECT UserId FROM User WHERE UserEmail=? AND UserId!=?", (email, staff_id))
        if cursor.fetchone():
            flash("This email is already in use.", "error")
            return redirect(url_for("editStaffProfile"))

        cursor.execute("UPDATE User SET FullName=?, UserEmail=?, Contact=? WHERE UserId=?", (name, email, contact, staff_id))
        db.commit()
        flash("Profile updated!", "success")
        return redirect(url_for("staffProfile"))

    cursor.execute("SELECT UserId, Fullname, UserEmail, Contact FROM User WHERE UserId=?", (staff_id,))
    staff = cursor.fetchone()
    return render_template("editStaffProfile.html", Staff=staff)


@app.route("/manageTrekS/<int:trekId>", methods=["GET", "POST"])
@role_required("Staff")
def manageTrekS(trekId):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT StaffId FROM Trek WHERE TrekId=?", (trekId,))
    trek = cursor.fetchone()
    if not trek or trek["StaffId"] != session.get("UserId"):
        return render_template("unauthorized.html"), 403

    if request.method == "POST":
        try:
            slot = int(request.form.get("Slot"))
        except (TypeError, ValueError):
            flash("Slot must be a number.", "error")
            return redirect(url_for("manageTrekS", trekId=trekId))

        if slot <= 0:
            flash("Slots must be greater than 0.", "error")
            return redirect(url_for("manageTrekS", trekId=trekId))

        status = request.form.get("Status")
        cursor.execute("SELECT Participants FROM Trek WHERE TrekId=?", (trekId,))
        p = cursor.fetchone()["Participants"]

        if slot < p:
            flash("Slot capacity cannot be lower than active participant count.", "error")
            return redirect(url_for("manageTrekS", trekId=trekId))

        cursor.execute("UPDATE Trek SET Slot=?, Status=? WHERE TrekId=?", (slot, status, trekId))
        db.commit()
        flash("Trek details updated.", "success")
        return redirect(url_for("assignedTreks"))

    cursor.execute("SELECT * FROM Trek WHERE TrekId=?", (trekId,))
    t = cursor.fetchone()
    return render_template("manageTrekS.html", trek=t)


@app.route("/markOngoing/<int:trekId>")
@role_required("Staff")
def markOngoing(trekId):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT StaffId, Status FROM Trek WHERE TrekId=?", (trekId,))
    trek = cursor.fetchone()
    if not trek or trek["StaffId"] != session.get("UserId"):
        return render_template("unauthorized.html"), 403

    if trek["Status"] != "Open":
        flash("Only an open trek can be marked as ongoing.", "warning")
        return redirect(url_for("manageTrekS", trekId=trekId))

    cursor.execute("UPDATE Trek SET Status='Ongoing' WHERE TrekId=?", (trekId,))
    db.commit()
    flash("Trek is now set to Ongoing.", "success")
    return redirect(url_for("assignedTreks"))


@app.route("/markCompleted/<int:trekId>")
@role_required("Staff")
def markCompleted(trekId):
    db = get_db()
    cursor = db.cursor()
    staff_id = session.get("UserId")

    cursor.execute("SELECT StaffId, Status FROM Trek WHERE TrekId=?", (trekId,))
    trek = cursor.fetchone()
    if not trek or trek["StaffId"] != staff_id:
        return render_template("unauthorized.html"), 403

    if trek["Status"] != "Ongoing":
        flash("Only ongoing treks can be marked as completed.", "error")
        return redirect(url_for("manageTrekS", trekId=trekId))

    cursor.execute("""SELECT b.BookingId, u.UserId as TrekkerId, u.FullName as TrekkerName, t.TrekId, t.TrekName, t.StaffId, s.FullName as StaffName, t.StartDate, t.EndDate, b.BookingDate
                      FROM Trek t 
                      JOIN Booking b ON t.TrekId=b.TrekId 
                      JOIN User u ON b.UserId=u.UserId 
                      LEFT JOIN User s ON s.UserId=t.StaffId 
                      WHERE t.TrekId=? AND t.StaffId=?""", (trekId, staff_id))
    bookings = cursor.fetchall()

    for rec in bookings:
        cursor.execute("""INSERT INTO History(BookingId, TrekkerId, TrekkerName, TrekId, TrekName, StaffId, StaffName, TrekStart, TrekEnd, BookingDate, Status) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Completed')""", tuple(rec))

    cursor.execute("DELETE FROM Trek WHERE TrekId=?", (trekId,))
    db.commit()
    flash("Trek completed and logged into history.", "success")
    return redirect(url_for("assignedTreks"))


@app.route("/removeParticipant/<int:trekkerId>/<int:trekId>")
@role_required("Staff")
def removeParticipant(trekkerId, trekId):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT StaffId FROM Trek WHERE TrekId=?", (trekId,))
    trek = cursor.fetchone()
    if not trek or trek["StaffId"] != session.get("UserId"):
        return render_template("unauthorized.html"), 403

    cursor.execute("SELECT BookingId FROM Booking WHERE UserId=? AND TrekId=?", (trekkerId, trekId))
    booking = cursor.fetchone()
    if not booking:
        flash("Booking not found.", "error")
        return redirect(url_for("staffTrekkers"))

    b_id = booking["BookingId"]
    cursor.execute("""SELECT b.BookingId, u.UserId, u.FullName, t.TrekId, t.TrekName, t.StaffId, s.FullName, t.StartDate, t.EndDate, b.BookingDate, 'Revoked' 
                      FROM Booking b 
                      JOIN Trek t ON b.TrekId=t.TrekId 
                      JOIN User u ON b.UserId=u.UserId 
                      LEFT JOIN User s ON t.StaffId=s.UserId 
                      WHERE b.BookingId=?""", (b_id,))
    hist_data = cursor.fetchone()
    if hist_data:
        cursor.execute("INSERT INTO History VALUES (?,?,?,?,?,?,?,?,?,?,?)", tuple(hist_data))

    cursor.execute("DELETE FROM Booking WHERE BookingId=?", (b_id,))
    cursor.execute("UPDATE Trek SET Participants = MAX(0, Participants - 1) WHERE TrekId=?", (trekId,))
    db.commit()
    flash("Participant removed from trek.", "success")
    return redirect(url_for("staffTrekkers"))


@app.route('/trekkerDashboard')
@role_required("Trekker")
def trekkerDashboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT TrekId, TrekName, Location, Difficulty, Duration_HRS, Slot - Participants as AvailableSlots, Price FROM Trek WHERE Status='Open' AND Slot - Participants > 0 LIMIT 5")
    a_treks = cursor.fetchall()

    user_id = session.get("UserId")
    cursor.execute("SELECT * FROM User WHERE UserId=?", (user_id,))
    user_info = cursor.fetchone()
    return render_template("trekkerDashboard.html", aTreks=a_treks, userInfo=user_info)


@app.route('/trekkerProfile')
@role_required("Trekker")
def trekkerProfile():
    db = get_db()
    cursor = db.cursor()
    user_id = session.get("UserId")
    cursor.execute("SELECT UserId, FullName, UserEmail, Contact FROM User WHERE UserId=?", (user_id,))
    trekker = cursor.fetchone()
    cursor.execute("SELECT count(TrekId) FROM History WHERE TrekkerId=?", (user_id,))
    c = cursor.fetchone()[0]
    return render_template("trekkerProfile.html", c=c, Trekker=trekker)


@app.route("/editTrekkerProfile", methods=["GET", "POST"])
@role_required("Trekker")
def editTrekkerProfile():
    db = get_db()
    cursor = db.cursor()
    user_id = session.get("UserId")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        contact = request.form.get("contact", "").strip()

        cursor.execute("SELECT UserId FROM User WHERE UserEmail=? AND UserId!=?", (email, user_id))
        if cursor.fetchone():
            flash("This email is already in use.", "error")
            return redirect(url_for("editTrekkerProfile"))

        cursor.execute("UPDATE User SET FullName=?, UserEmail=?, Contact=? WHERE UserId=?", (name, email, contact, user_id))
        db.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("trekkerProfile"))

    cursor.execute("SELECT UserId, FullName, UserEmail, Contact FROM User WHERE UserId=?", (user_id,))
    trekker = cursor.fetchone()
    return render_template("editTrekkerProfile.html", Trekker=trekker)


@app.route("/trekkerTreks", methods=["GET", "POST"])
@role_required("Trekker")
def trekkerTreks():
    db = get_db()
    cursor = db.cursor()
    user_id = session.get("UserId")

    if request.method == "POST":
        location = request.form.get("Location", "").strip()
        difficulty = request.form.get("Difficulty", "").strip()
        if difficulty == "Any":
            difficulty = None

        if not location and not difficulty:
            flash("Please specify location or difficulty filter.", "warning")
            return redirect(url_for("trekkerTreks"))

        query = """SELECT t.TrekId, t.TrekName, t.Difficulty, t.Location, t.Duration_HRS, t.Slot - t.Participants as AvailableSlots, t.StartDate, t.Status, s.FullName as StaffName, s.Contact as StaffContact, t.Price 
                   FROM Trek t 
                   LEFT JOIN User s ON t.StaffId=s.UserId 
                   WHERE t.Status='Open' AND t.Slot - t.Participants > 0 
                   AND NOT EXISTS (SELECT 1 FROM Booking b WHERE t.TrekId=b.TrekId AND b.UserId=?)"""
        params = [user_id]

        if difficulty:
            query += " AND t.Difficulty=?"
            params.append(difficulty)
        if location:
            query += " AND t.Location LIKE ?"
            params.append(f"%{location}%")

        cursor.execute(query, params)
        a_treks = cursor.fetchall()
        return render_template("trekkerTreks.html", aTreks=a_treks)

    cursor.execute("""SELECT t.TrekId, t.TrekName, t.Difficulty, t.Location, t.Duration_HRS, t.Slot - t.Participants as AvailableSlots, t.StartDate, t.Status, s.FullName as StaffName, s.Contact as StaffContact, t.Price 
                      FROM Trek t 
                      LEFT JOIN User s ON t.StaffId=s.UserId 
                      WHERE t.Status='Open' AND t.Slot - t.Participants > 0 
                      AND NOT EXISTS (SELECT 1 FROM Booking b WHERE t.TrekId=b.TrekId AND b.UserId=?)""", (user_id,))
    a_treks = cursor.fetchall()
    return render_template("trekkerTreks.html", aTreks=a_treks)


@app.route("/bookTrek/<int:TrekId>", methods=["GET", "POST"])
@role_required("Trekker")
def bookTrek(TrekId):
    db = get_db()
    cursor = db.cursor()
    user_id = session.get("UserId")

    if razorpay_client is None:
        flash("Online payments are not configured. Please contact the administrator.", "error")
        return redirect(url_for("trekkerTreks"))

    cursor.execute("SELECT BookingId FROM Booking WHERE UserId=? AND TrekId=? AND BookingStatus='Booked'", (user_id, TrekId))
    if cursor.fetchone():
        flash("You have already booked this trek!", "warning")
        return redirect(url_for("bookedTreks"))

    cursor.execute("SELECT TrekId, TrekName, Participants, Slot, Status, Price FROM Trek WHERE TrekId=?", (TrekId,))
    trek = cursor.fetchone()
    if not trek:
        return "Trek Not Found", 404

    if trek["Status"] != "Open" or trek["Participants"] >= trek["Slot"]:
        flash("Sorry, this trek is no longer available for booking.", "warning")
        return redirect(url_for("trekkerTreks"))

    cursor.execute("SELECT FullName, UserEmail, Contact FROM User WHERE UserId=?", (user_id,))
    user_info = cursor.fetchone()

    amount_in_paise = int(round(float(trek["Price"]) * 100))
    try:
        order_data = {
            "amount": amount_in_paise,
            "currency": RAZORPAY_CURRENCY,
            "receipt": f"receipt_trek_{TrekId}_user_{user_id}",
            "payment_capture": 1
        }
        razorpay_order = razorpay_client.order.create(data=order_data)
    except Exception:
        app.logger.exception("Razorpay order creation failed for trek %s and user %s", TrekId, user_id)
        flash("Unable to start payment. Please try again.", "error")
        return redirect(url_for("trekkerTreks"))

    session["razorpay_order_id"] = razorpay_order["id"]
    session["razorpay_trek_id"] = TrekId

    return render_template("bookTrek.html",
                           trek=trek,
                           userInfo=user_info,
                           razorpay_order_id=razorpay_order["id"],
                           razorpay_key_id=RAZORPAY_KEY_ID,
                           amount=amount_in_paise,
                           price_in_rs=trek["Price"],
                           currency=RAZORPAY_CURRENCY)


@app.route("/verifyPayment", methods=["POST"])
@role_required("Trekker")
def verifyPayment():
    user_id = session.get("UserId")
    trek_id = request.form.get("trek_id")
    razorpay_payment_id = request.form.get("razorpay_payment_id")
    razorpay_order_id = request.form.get("razorpay_order_id")
    razorpay_signature = request.form.get("razorpay_signature")

    if not trek_id or not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
        flash("Invalid booking request.", "error")
        return redirect(url_for("trekkerTreks"))

    try:
        trek_id_val = int(trek_id)
    except (ValueError, TypeError):
        flash("Invalid booking request.", "error")
        return redirect(url_for("trekkerTreks"))

    if (razorpay_client is None
            or session.get("razorpay_order_id") != razorpay_order_id
            or session.get("razorpay_trek_id") != trek_id_val):
        flash("Payment verification failed! Please try again.", "error")
        return redirect(url_for("trekkerTreks"))

    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })
    except Exception:
        app.logger.exception("Razorpay payment verification failed for order %s", razorpay_order_id)
        flash("Payment verification failed! Please try again.", "error")
        return redirect(url_for("trekkerTreks"))

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT Participants, Slot, Status FROM Trek WHERE TrekId=?", (trek_id,))
    trek = cursor.fetchone()
    if not trek or trek["Status"] != "Open" or trek["Participants"] >= trek["Slot"]:
        flash("Booking failed: Trek slots are full.", "error")
        return redirect(url_for("trekkerTreks"))

    cursor.execute("""INSERT INTO Booking (UserId, TrekId, BookingStatus, BookingDate, PaymentStatus, RazorpayOrderId, RazorpayPaymentId) 
                      VALUES (?, ?, 'Booked', ?, 'Done', ?, ?)""",
                   (user_id, trek_id, date.today(), razorpay_order_id, razorpay_payment_id))

    cursor.execute("UPDATE Trek SET Participants = Participants + 1 WHERE TrekId=?", (trek_id,))
    db.commit()

    session.pop("razorpay_order_id", None)
    session.pop("razorpay_trek_id", None)

    flash("Payment successful! Your trek booking is confirmed.", "success")
    return redirect(url_for("bookedTreks"))


@app.route("/bookedTreks")
@role_required("Trekker")
def bookedTreks():
    db = get_db()
    cursor = db.cursor()
    user_id = session.get("UserId")
    cursor.execute("""SELECT b.BookingId, t.TrekName, b.BookingDate, t.StartDate, t.Duration_HRS, b.BookingStatus, b.PaymentStatus, t.EndDate, s.FullName as StaffName, s.Contact as StaffContact, t.Difficulty, t.Location, t.Price 
                      FROM Booking b 
                      JOIN Trek t ON b.TrekId=t.TrekId 
                      LEFT JOIN User s ON s.UserId=t.StaffId 
                      WHERE b.UserId=?""", (user_id,))
    bookings = cursor.fetchall()
    return render_template("bookedTreks.html", bookings=bookings)


@app.route("/cancelBooking/<int:BookingId>")
@role_required("Trekker")
def cancelBooking(BookingId):
    db = get_db()
    cursor = db.cursor()
    user_id = session.get("UserId")

    cursor.execute("""SELECT b.BookingId, b.TrekId, b.BookingStatus, t.StartDate, t.Status 
                      FROM Booking b 
                      JOIN Trek t ON t.TrekId=b.TrekId 
                      WHERE b.BookingId=? AND b.UserId=?""", (BookingId, user_id))
    booking = cursor.fetchone()

    if not booking or booking["BookingStatus"] != "Booked":
        flash("Invalid booking or booking cannot be cancelled.", "error")
        return redirect(url_for("bookedTreks"))

    try:
        start_dt = datetime.strptime(booking["StartDate"].strip(), "%Y-%m-%d").date()
        if start_dt <= date.today():
            flash("Cannot cancel booking on or after trek start date.", "warning")
            return redirect(url_for("bookedTreks"))
    except ValueError:
        pass

    cursor.execute("""SELECT b.BookingId, u.UserId, u.FullName, t.TrekId, t.TrekName, t.StaffId, s.FullName, t.StartDate, t.EndDate, b.BookingDate, 'Cancelled' 
                      FROM Booking b 
                      JOIN Trek t ON b.TrekId=t.TrekId 
                      JOIN User u ON b.UserId=u.UserId 
                      LEFT JOIN User s ON t.StaffId=s.UserId 
                      WHERE b.BookingId=?""", (BookingId,))
    data = cursor.fetchone()
    if data:
        cursor.execute("INSERT INTO History VALUES (?,?,?,?,?,?,?,?,?,?,?)", tuple(data))

    cursor.execute("DELETE FROM Booking WHERE BookingId=?", (BookingId,))
    cursor.execute("UPDATE Trek SET Participants = MAX(0, Participants - 1) WHERE TrekId=?", (booking["TrekId"],))
    db.commit()

    flash("Booking cancelled successfully.", "success")
    return redirect(url_for("bookedTreks"))


@app.route("/trekkerHistory")
@role_required("Trekker")
def trekkerHistory():
    db = get_db()
    cursor = db.cursor()
    user_id = session.get("UserId")
    cursor.execute("SELECT BookingId, TrekName, BookingDate, TrekStart, TrekEnd, Status FROM History WHERE TrekkerId=?", (user_id,))
    trekkings = cursor.fetchall()
    return render_template("trekkerHistory.html", trekkings=trekkings)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)