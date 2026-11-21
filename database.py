import os
import sqlite3
from datetime import date, timedelta


DATABASE = os.path.join(os.path.dirname(__file__), "TrekManagement.db")


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
        ImagePath TEXT,
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
    if 'ImagePath' not in trek_cols:
        cursor.execute("ALTER TABLE Trek ADD COLUMN ImagePath TEXT;")

    cursor.execute("""CREATE TABLE IF NOT EXISTS EmailVerification (
        Email TEXT NOT NULL,
        Purpose TEXT NOT NULL,
        OTPHash TEXT NOT NULL,
        ExpiresAt TEXT NOT NULL,
        CreatedAt TEXT NOT NULL,
        Attempts INTEGER NOT NULL DEFAULT 0,
        Payload TEXT,
        PRIMARY KEY (Email, Purpose)
    );""")

    cursor.execute("PRAGMA table_info(Booking)")
    booking_cols = [col[1] for col in cursor.fetchall()]
    if 'RazorpayOrderId' not in booking_cols:
        cursor.execute("ALTER TABLE Booking ADD COLUMN RazorpayOrderId TEXT;")
    if 'RazorpayPaymentId' not in booking_cols:
        cursor.execute("ALTER TABLE Booking ADD COLUMN RazorpayPaymentId TEXT;")

    demo_users = [
        ("Gaurav", "aroraganesh2007@gmail.com", "Admin", "9999999999"),
        ("Rohan Mehta", "trekker@example.com", "Trekker", "9999999998"),
        ("Vikram Joshi", "staff@example.com", "Staff", "9999999997"),
        ("Aarav Sharma", "aarav@example.com", "Trekker", "9999999996"),
        ("Meera Patel", "meera@example.com", "Trekker", "9999999995"),
        ("Kabir Singh", "kabir@example.com", "Trekker", "9999999994"),
        ("Ananya Rao", "ananya@example.com", "Trekker", "9999999993"),
        ("Ishaan Verma", "ishaan@example.com", "Trekker", "9999999992"),
        ("Riya Nair", "riya@example.com", "Trekker", "9999999991"),
        ("Dev Malhotra", "dev@example.com", "Trekker", "9999999990"),
        ("Neha Kapoor", "neha@example.com", "Trekker", "9999999989"),
        ("Priya Menon", "priya.staff@example.com", "Staff", "9999999988"),
        ("Arjun Das", "arjun.staff@example.com", "Staff", "9999999987"),
    ]
    demo_password = "15022026"
    for full_name, email, role, contact in demo_users:
        cursor.execute("SELECT UserId, FullName FROM User WHERE UserEmail=?", (email,))
        existing_user = cursor.fetchone()
        if existing_user is None:
            cursor.execute("INSERT INTO User (FullName, UserEmail, UserPassword, UserRole, Contact) VALUES (?, ?, ?, ?, ?)",
                           (full_name, email, demo_password, role, contact))
        elif existing_user[1] in ("Sample Trekker", "Sample Staff"):
            cursor.execute("UPDATE User SET FullName=?, Contact=? WHERE UserId=?",
                           (full_name, contact, existing_user[0]))

    demo_staff_requests = [
        ("Sanjay Kulkarni", "sanjay.request@example.com", "9876501234"),
        ("Lakshmi Krishnan", "lakshmi.request@example.com", "9876501235"),
    ]
    for name, email, contact in demo_staff_requests:
        cursor.execute("SELECT ReqId FROM StaffReq WHERE Email=? UNION SELECT UserId FROM User WHERE UserEmail=?", (email, email))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO StaffReq (Name, Email, Password, Contact) VALUES (?, ?, ?, ?)",
                           (name, email, demo_password, contact))

    demo_treks = [
        ("Dzongri Viewpoint Trek", "Moderate", "Sikkim", 24, 14, 18, 12, 2, "Open", 4800, "staff@example.com"),
        ("Kalsubai Sunrise Challenge", "Difficult", "Maharashtra", 8, 21, 22, 8, 8, "Open", 1600, "priya.staff@example.com"),
        ("Rajmachi Fort Night Trail", "Easy", "Maharashtra", 10, 28, 29, 8, 8, "Open", 1400, "arjun.staff@example.com"),
        ("Kudremukh Forest Crossing", "Moderate", "Karnataka", 18, -1, 1, 12, 3, "Ongoing", 3600, "priya.staff@example.com"),
        ("Nilgiri Ridge Walk", "Easy", "Tamil Nadu", 12, 35, 36, 10, 0, "Closed", 2200, "arjun.staff@example.com"),
        ("Bhrigu Lake Alpine Trek", "Difficult", "Himachal Pradesh", 32, 42, 46, 14, 0, "Open", 5200, None),
        ("Valley of Flowers Trail", "Moderate", "Uttarakhand", 24, 56, 60, 16, 0, "Open", 4300, "staff@example.com"),
        ("Chembra Peak Forest Hike", "Easy", "Kerala", 8, 70, 71, 10, 0, "Open", 1900, "priya.staff@example.com"),
    ]
    for name, difficulty, location, duration, start_offset, end_offset, slots, participants, status, price, staff_email in demo_treks:
        cursor.execute("SELECT TrekId FROM Trek WHERE TrekName=?", (name,))
        if cursor.fetchone() is not None:
            continue
        staff_id = None
        if staff_email:
            cursor.execute("SELECT UserId FROM User WHERE UserEmail=? AND UserRole='Staff'", (staff_email,))
            staff_id = cursor.fetchone()[0]
        start_date = date.today() + timedelta(days=start_offset)
        end_date = date.today() + timedelta(days=end_offset)
        cursor.execute("""INSERT INTO Trek (TrekName, Difficulty, Location, Duration_HRS, StartDate, EndDate, Slot, StaffId, Status, Participants, Price)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (name, difficulty, location, duration, start_date, end_date, slots, staff_id, status, participants, price))

    demo_bookings = [
        ("Dzongri Viewpoint Trek", "aarav@example.com"),
        ("Dzongri Viewpoint Trek", "meera@example.com"),
        ("Kalsubai Sunrise Challenge", "kabir@example.com"),
        ("Kalsubai Sunrise Challenge", "ananya@example.com"),
        ("Kalsubai Sunrise Challenge", "ishaan@example.com"),
        ("Kalsubai Sunrise Challenge", "riya@example.com"),
        ("Kalsubai Sunrise Challenge", "dev@example.com"),
        ("Kalsubai Sunrise Challenge", "neha@example.com"),
        ("Kalsubai Sunrise Challenge", "aarav@example.com"),
        ("Kalsubai Sunrise Challenge", "meera@example.com"),
        ("Rajmachi Fort Night Trail", "aarav@example.com"),
        ("Rajmachi Fort Night Trail", "meera@example.com"),
        ("Rajmachi Fort Night Trail", "kabir@example.com"),
        ("Rajmachi Fort Night Trail", "ananya@example.com"),
        ("Rajmachi Fort Night Trail", "ishaan@example.com"),
        ("Rajmachi Fort Night Trail", "riya@example.com"),
        ("Rajmachi Fort Night Trail", "dev@example.com"),
        ("Rajmachi Fort Night Trail", "neha@example.com"),
        ("Kudremukh Forest Crossing", "aarav@example.com"),
        ("Kudremukh Forest Crossing", "meera@example.com"),
        ("Kudremukh Forest Crossing", "kabir@example.com"),
    ]
    for trek_name, trekker_email in demo_bookings:
        cursor.execute("SELECT TrekId FROM Trek WHERE TrekName=?", (trek_name,))
        trek_id = cursor.fetchone()[0]
        cursor.execute("SELECT UserId FROM User WHERE UserEmail=? AND UserRole='Trekker'", (trekker_email,))
        trekker_id = cursor.fetchone()[0]
        cursor.execute("SELECT BookingId FROM Booking WHERE UserId=? AND TrekId=?", (trekker_id, trek_id))
        if cursor.fetchone() is None:
            cursor.execute("""INSERT INTO Booking (UserId, TrekId, BookingStatus, BookingDate, PaymentStatus)
                              VALUES (?, ?, 'Booked', ?, 'Demo')""",
                           (trekker_id, trek_id, date.today() - timedelta(days=2)))

    for trek_name, *_ in demo_treks:
        cursor.execute("""UPDATE Trek SET Participants=(
                              SELECT COUNT(*) FROM Booking
                              WHERE Booking.TrekId=Trek.TrekId AND Booking.BookingStatus='Booked'
                          ) WHERE TrekName=?""", (trek_name,))

    demo_history = [
        ("aarav@example.com", "Chadar Frozen River Trek", "Ladakh", "Completed", 100, 94, 90, "staff@example.com"),
        ("meera@example.com", "Kalsubai Monsoon Trail", "Maharashtra", "Cancelled", 45, 38, 35, "priya.staff@example.com"),
        ("kabir@example.com", "Gokarna Coastal Trek", "Karnataka", "Revoked", 30, 23, 20, "arjun.staff@example.com"),
    ]
    for index, (trekker_email, trek_name, location, status, booking_offset, start_offset, end_offset, staff_email) in enumerate(demo_history, start=1):
        cursor.execute("SELECT 1 FROM History WHERE TrekName=? AND TrekkerId=(SELECT UserId FROM User WHERE UserEmail=?) AND Status=?",
                       (trek_name, trekker_email, status))
        if cursor.fetchone() is not None:
            continue
        cursor.execute("SELECT UserId, FullName FROM User WHERE UserEmail=?", (trekker_email,))
        trekker_id, trekker_name = cursor.fetchone()
        cursor.execute("SELECT UserId, FullName FROM User WHERE UserEmail=?", (staff_email,))
        staff_id, staff_name = cursor.fetchone()
        cursor.execute("SELECT COALESCE(MAX(BookingId), 0) + 1 FROM (SELECT BookingId FROM Booking UNION ALL SELECT BookingId FROM History)")
        booking_id = cursor.fetchone()[0]
        cursor.execute("""INSERT INTO History (BookingId, TrekkerId, TrekkerName, TrekId, TrekName, StaffId, StaffName, TrekStart, TrekEnd, BookingDate, Status)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                       (booking_id, trekker_id, trekker_name, -index, trek_name, staff_id, staff_name,
                        date.today() - timedelta(days=start_offset), date.today() - timedelta(days=end_offset),
                        date.today() - timedelta(days=booking_offset), status))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()