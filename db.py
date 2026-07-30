import sqlite3

conn=sqlite3.connect("TrekManagement.db")

cursor=conn.cursor()

cursor.execute("""Create table User (
               UserId INTEGER PRIMARY KEY autoincrement,
               FullName TEXT,
               UserEmail TEXT,
               UserPassword TEXT,
               UserRole TEXT,
               Contact TEXT
               );""")

cursor.execute("""Create table Trek (
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

cursor.execute("""Create table Booking (
               BookingId INTEGER PRIMARY KEY autoincrement,
               UserId INTEGER, 
               TrekId INTEGER,
               BookingStatus TEXT,
               BookingDate TEXT,
               PaymentStatus TEXT,
               FOREIGN KEY(UserId) REFERENCES User(UserId) ON DELETE CASCADE,
               FOREIGN KEY(TrekId) REFERENCES Trek(TrekId) ON DELETE CASCADE
               );""")

cursor.execute("""Create table StaffReq (
               ReqId INTEGER PRIMARY KEY autoincrement,
               Name TEXT,
               Email TEXT,
               Password TEXT,
               Contact TEXT
               );""")

cursor.execute("""Create table History (
                BookingId INTEGER,
                TrekkerId INTEGER,
                TrekkerName TEXT,
                TrekId INTEGER,
                TrekName TEXT,
                StaffId INTEGER,
                StaffName TEXT,
                TrekStart DATE,
                Duration_HRS INTEGER
                );""")


cursor.execute("""INSERT INTO USER values(Null,"Gaurav","aroraganesh2007@gmail.com","2026","Admin",Null);""")

conn.commit()
conn.close()