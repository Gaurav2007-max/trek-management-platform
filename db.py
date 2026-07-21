import sqlite3

conn=sqlite3.connect("TrekManagement.db")

cursor=conn.cursor()

cursor.execute("""Create table User (
               UserId INTEGER PRIMARY KEY autoincrement,
               FullName TEXT,
               UserEmail TEXT,
               UserPassword TEXT,
               UserRole TEXT,
               Contact TEXT);""")

cursor.execute("""Create table Trek (
               TrekId INTEGER PRIMARY KEY autoincrement,
               TrekName TEXT,
               Difficulty TEXT,
               Location TEXT,
               Duration TEXT,
               Slot INTEGER,
               StaffId INTEGER,
               Status text,
               FOREIGN KEY(StaffId) REFERENCES User("UserId")
               );""")

cursor.execute("""Create table Booking (
               BookingId INTEGER PRIMARY KEY autoincrement,
               UserId INTEGER, 
               TrekId INTEGER,
               BookingStatus TEXT,
               BookingDate TEXT,
               PaymentStatus TEXT,
               FOREIGN KEY(UserId) REFERENCES User("UserId"),
               FOREIGN KEY(TrekId) REFERENCES Trek("TrekId")
               );""")

cursor.execute("""Create table StaffReq (
               ReqId INTEGER PRIMARY KEY autoincrement,
               Name TEXT,
               Email TEXT,
               Contact TEXT,
               Password TEXT
               );""")

cursor.execute("""INSERT INTO USER values(Null,"Gaurav","aroraganesh2007@gmail.com","2026","Admin",Null);""")

conn.commit()
conn.close()