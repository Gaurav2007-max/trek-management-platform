import sqlite3

conn=sqlite3.connect("TrekManagement.db")

cursor=conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS User (
               UserId INTEGER PRIMARY KEY autoincrement,
               FullName TEXT,
               UserEmail TEXT UNIQUE,
               UserPassword TEXT,
               UserRole TEXT,
               Contact TEXT
               );""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Trek (
               TrekId INTEGER PRIMARY KEY autoincrement,
               TrekName TEXT Not Null,
               Difficulty TEXT,
               Location TEXT,
               Duration_HRS INTEGER,
               StartDate DATE,
               EndDate DATE,
               Slot INTEGER,
               StaffId INTEGER,
               Status TEXT,
               Participants INTEGER Default 0,
               FOREIGN KEY(StaffId) REFERENCES User(UserId) ON DELETE SET NULL
               );""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Booking (
               BookingId INTEGER PRIMARY KEY autoincrement,
               UserId INTEGER, 
               TrekId INTEGER,
               BookingStatus TEXT,
               BookingDate Date,
               PaymentStatus TEXT,
               FOREIGN KEY(UserId) REFERENCES User(UserId) ON DELETE CASCADE,
               FOREIGN KEY(TrekId) REFERENCES Trek(TrekId) ON DELETE CASCADE
               );""")

cursor.execute("""CREATE TABLE IF NOT EXISTS StaffReq (
               ReqId INTEGER PRIMARY KEY autoincrement,
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
                TrekEnd Date,
                BookingDate Date,
                Status TEXT
                );""")
cursor.execute("Select * from User where UserEmail='aroraganesh2007@gmail.com'")
row=cursor.fetchone()
if(not row):
   cursor.execute("""INSERT INTO USER values(Null,"Gaurav","aroraganesh2007@gmail.com","15022026","Admin",Null);""")
conn.commit()
conn.close()