from flask import Flask, render_template, request, redirect, url_for,flash,session
import sqlite3 
from datetime import date
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

app=Flask(__name__)
app.secret_key="trekker"

def checkAdmin():
    if("UserId" not in session):
        flash("Please login first","warning")
        return redirect("/login")
    if(session.get('Role')!='Admin'):
        flash("You do not have access to this page or action","warning")
        return render_template("unauthorized.html"),403
    return

def checkStaff():
    if("UserId" not in session):
        flash("Please login first","warning")
        return redirect("/login")
    if(session.get('Role')!='Staff'):
        flash("You do not have access to this page or action","warning")
        return render_template("unauthorized.html"),403
    return

def checkTrekker():
    if("UserId" not in session):
        flash("Please login first","warning")
        return redirect("/login")
    if(session.get('Role')!='Trekker'):
        flash("You do not have access to this page or action","warning")
        return render_template("unauthorized.html"),403
    return


@app.route('/',methods=["GET","POST"])
def index():
    if "UserId" in session:
        Id=session.get("UserId")
        Role=session.get("Role")
        if(Role):
            if(Role=="Admin"):
                return redirect(url_for("adminDashboard"))
            elif(Role=="Staff"):
                return redirect(url_for("staffDashboard"))
            else:
                return redirect(url_for("trekkerDashboard"))
        else:
            flash("No Data found in database","error")
            return redirect(url_for("login"))
    else:
        return redirect(url_for("login"))
        

@app.route('/login',methods=["GET","POST"])
def login():
    if(request.method=="POST"):
        conn=sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor=conn.cursor()
        username=request.form.get("Username")
        password=request.form.get("Password")
        if not username or not password:
            conn.close()
            flash("All fields required","warning")
            return redirect("/login")
        cursor.execute("Select * from User where UserEmail=? AND UserPassword=?",(username,password))
        row=cursor.fetchone()
        userInfo=row
        conn.close()
        if row:
            Role=row[4]
        else:
            flash("User not found","warning")
            return redirect(url_for("login"))
        if(userInfo):
            session['UserId']=userInfo[0]
            session['Role']=userInfo[4]
            if(userInfo[4]=="Admin"):
                return redirect(url_for("adminDashboard"))
            elif(userInfo[4]=="Staff"):
                return redirect(url_for("staffDashboard"))
            else:
                return redirect(url_for("trekkerDashboard"))
        else:
            flash("Invalid username or password","error")
            return redirect(url_for("login"))
        
    return render_template("login.html")

@app.route('/register',methods=["GET","POST"])
def register():
    if(request.method=="POST"):
        conn=sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor=conn.cursor()
        name=request.form.get("Fullname")
        email=request.form.get("Email")
        cursor.execute("Select UserEmail from User where UserEmail=?",(email,))
        data=cursor.fetchone()
        
        if(data):
            flash("Email already in use","error")
            conn.close()
            return redirect('/register')
        
        cursor.execute("Select Email from StaffReq where Email=?",(email,))
        data=cursor.fetchone()
        if(data):
            flash("Already requested please wait for admin approval","warning")
            conn.close()
            return redirect('/register')

        password=request.form.get("Password")
        password2=request.form.get("Password2")
        contact=request.form.get("Contact")
        role=request.form.get("Role")
        if not name or not password or not password2 or not email or not contact or not role:
            conn.close()
            flash("All fields required","warning")
            return redirect("/register")
        if(password!=password2):
            flash("Please enter same password for confirmation","error")
            conn.close()
            return redirect('/register')
        if(role=="Trekker"):
            cursor.execute("Insert into User (UserId,FullName,UserEmail,UserPassword,UserRole,Contact) values(?,?,?,?,?,?)",(None,name,email,password,role,contact))
            conn.commit()
            conn.close()
            flash("Successfully registered as Trekker","success")
            return redirect('/login')
        elif role=="Staff":
            cursor.execute("Insert into StaffReq (ReqId,Name,Email,Password,Contact) values(?,?,?,?,?)",(None,name,email,password,contact))
            conn.commit()
            conn.close()
            flash("Request Sent to Admin, You can login once admin approves","success")
            return redirect('/')
        else:
            flash("Invalid Inputs","error")
            conn.close()
            return redirect('/register')
    return render_template("register.html")

@app.route('/adminDashboard')
def adminDashboard():
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("Select count(TrekId) from Trek")
    TotalTreks=cursor.fetchone()[0]
    cursor.execute("Select count(UserId) from User where UserRole='Trekker'")
    TotalUsers=cursor.fetchone()[0]
    cursor.execute("Select count(UserId) from User where UserRole='Staff'")
    TotalStaff=cursor.fetchone()[0]
    cursor.execute("Select count(BookingId) from Booking")
    TotalBookings=cursor.fetchone()[0]
    cursor.execute("Select BookingId,FullName,TrekName,BookingStatus,BookingDate from Booking b, Trek t, User U where b.TrekId=t.TrekId and b.UserId=U.UserId Order By BookingDate DESC limit 5")
    bookings=cursor.fetchall()  
    Id=session.get("UserId")
    cursor.execute("Select * from User where UserId=?",(Id,))  
    UserInfo=cursor.fetchone()
    conn.close()
    return render_template("adminDashboard.html",TotalTreks=TotalTreks,TotalUsers=TotalUsers,TotalStaff=TotalStaff,TotalBookings=TotalBookings,bookings=bookings,UserInfo=UserInfo)

@app.route('/addTrek',methods=["GET","POST"])
def addTrek():
    response=checkAdmin()
    if response:
        return response
    if(request.method=="POST"):
        conn=sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor=conn.cursor()
        TrekName=request.form.get("Trekname")
        TrekDifficulty=request.form.get("Difficulty")
        TrekLocation=request.form.get("Location")
        TrekDuration=request.form.get("Duration")
        TrekS=request.form.get("sDate")
        TrekE=request.form.get("eDate")
        TrekSlot=request.form.get("Slot")
        TrekStaff=request.form.get("StaffId")
        if not TrekName or not TrekDifficulty or not TrekDuration or not TrekSlot or not TrekS or not TrekE or not TrekLocation:
            conn.close()
            flash("All fields are required","warning")
            return redirect(url_for("addTrek"))
        try:
            TrekDuration=int(TrekDuration)
            TrekSlot=int(TrekSlot)
        except ValueError:
            conn.close()
            flash("Duration and Slot must be numbers","error")
            return redirect(url_for("addTrek"))
        if TrekDuration<=0:
            conn.close()
            flash("Duration must be greater than 0","error")
            return redirect(url_for("addTrek"))
        if TrekSlot<=0:
            conn.close()
            flash("Slots must be greater than 0","error")
            return redirect(url_for("addTrek"))
        if TrekE<TrekS:
            conn.close()
            flash("End date must not be before start date","error")
            return redirect(url_for("addTrek"))
        if TrekStaff:
            try:
                TrekStaff=int(TrekStaff)
            except ValueError:
                conn.close()
                flash("Invalid staff ID","error")
                return redirect("/addTrek")
            cursor.execute("SELECT UserId FROM User WHERE UserId=? AND UserRole='Staff'",(TrekStaff,))
            if cursor.fetchone() is None:
                conn.close()
                flash("Invalid staff member","error")
                return redirect("/addTrek")
        else:
            TrekStaff=None
        cursor.execute("INSERT INTO Trek(TrekId,TrekName,Difficulty,Location,Duration_HRS,StartDate,EndDate,Slot,StaffId,Status) VALUES(?,?,?,?,?,?,?,?,?,'Open')",(None,TrekName,TrekDifficulty,TrekLocation,TrekDuration,TrekS,TrekE,TrekSlot,TrekStaff))
        conn.commit()
        conn.close()
        return redirect("/adminTreks")
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("Select UserId,Fullname from User where UserRole='Staff'")
    staffs=cursor.fetchall()
    conn.close()
    return render_template("addTrek.html",staffs=staffs)

@app.route("/adminTreks", methods=["GET","POST"])
def adminTreks():
    response=checkAdmin()
    if response:
        return response
    if(request.method=="POST"):
        NameorId=request.form.get("NameorId")
        if(NameorId):
            x=""
            y=1
            try:
                x=int(NameorId)
                y=0
            except ValueError:
                x=str(NameorId)
            return redirect(url_for("searchTrek",x=x,y=y))
        else:
            flash("Please search after putting values", "warning")
            return redirect(url_for("adminTreks"))

    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("Select * from Trek")
    treks=cursor.fetchall()
    conn.close()
    return render_template("adminTreks.html",treks=treks)

@app.route("/editTrek/<int:TrekId>",methods=["GET","POST"])
def editTrek(TrekId):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    if(request.method=="POST"):
        TrekName=request.form.get("Trekname")
        TrekDifficulty=request.form.get("Difficulty")
        TrekLocation=request.form.get("Location")
        TrekDuration=request.form.get("Duration")
        TrekS=request.form.get("sDate")
        TrekE=request.form.get("eDate")
        TrekSlot=request.form.get("Slot")
        TrekStaff=request.form.get("StaffId")
        if not TrekName or not TrekDifficulty or not TrekDuration or not TrekSlot or not TrekS or not TrekE or not TrekLocation:
            conn.close()
            flash("All fields are required","warning")
            return redirect(url_for("editTrek",TrekId=TrekId))
        try:
            TrekDuration=int(TrekDuration)
            TrekSlot=int(TrekSlot)
        except ValueError:
            conn.close()
            flash("Duration and Slot must be numbers","error")
            return redirect(url_for("editTrek",TrekId=TrekId))
        if TrekDuration<=0:
            conn.close()
            flash("Duration must be greater than 0","error")
            return redirect(url_for("editTrek",TrekId=TrekId))
        if TrekSlot<=0:
            conn.close()
            flash("Slots must be greater than 0","error")
            return redirect(url_for("editTrek",TrekId=TrekId))
        if TrekE<TrekS:
            conn.close()
            flash("End date must be after start date","error")
            return redirect(url_for("editTrek",TrekId=TrekId))
        if TrekStaff:
            try:
                TrekStaff=int(TrekStaff)
                cursor.execute("SELECT * from User where UserId=? and UserRole='Staff'",(TrekStaff,))
                row=cursor.fetchone()
                if not row:
                    conn.close()
                    flash("The given staff was not found in database","error")
                    return redirect(url_for("editTrek",TrekId=TrekId))
            except ValueError:
                conn.close()
                flash("Invalid staff ID","error")
                return redirect(url_for("editTrek",TrekId=TrekId))
        else:
            TrekStaff=None
        cursor.execute("Select Participants from Trek where TrekId=?",(TrekId,))
        p=cursor.fetchone()[0]
        if(TrekSlot<p):
            conn.close()
            flash("Slots can not be less than bookings already booked","error")
            return redirect(url_for("editTrek",TrekId=TrekId))
        if(TrekStaff==""):
            TrekStaff=None
        TrekStatus=request.form.get("Status")
        if TrekE<TrekS:
            flash("End date must be after start date","error")
            conn.close()
            return redirect(url_for("editTrek",TrekId=TrekId))
        cursor.execute("""UPDATE Trek SET TrekName=?, Difficulty=?, Location=?, Duration_HRS=?, StartDate=?, EndDate=?, Slot=?, StaffId=?, Status=? WHERE TrekId=?""", (
            TrekName,TrekDifficulty,TrekLocation,TrekDuration,TrekS,TrekE,TrekSlot,TrekStaff,TrekStatus,TrekId))
        conn.commit()
        conn.close()
        flash("Trek has been updated","success")
        return redirect("/adminTreks")
    cursor.execute("Select * from Trek where TrekId=?",(TrekId,))
    trek=cursor.fetchone()
    if not trek:
        conn.close()
        return "Trek Not found",404
    cursor.execute("Select u.UserId from User u, Trek t where u.UserId=t.StaffId and t.TrekId=?",(TrekId,))
    row=cursor.fetchone()
    cursor.execute("Select UserId,Fullname from User where UserRole='Staff'")
    staffs=cursor.fetchall()
    if row:
        staffId=row[0]
    else:
        staffId=None
    conn.close()
    return render_template("editTrek.html",trek=trek,staffs=staffs,staffId=staffId)

@app.route("/removeTrek/<int:TrekId>")
def removeTrek(TrekId):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("SELECT BookingId from Booking where TrekId=?",(TrekId,))
    rows=cursor.fetchall()
    for row in rows:
        BookingId=row[0]
        cursor.execute("SELECT BookingId,u.UserId,u.Fullname,t.TrekId,t.TrekName,t.StaffId,s.Fullname,t.StartDate,t.EndDate,b.BookingDate,'Revoked' from Booking b Join Trek t on b.Trekid=t.TrekId Join User u on b.UserId=u.UserId LEFT Join User s on t.StaffId=s.UserId where b.BookingId=?",(BookingId,))
        data=cursor.fetchone()
        cursor.execute("INSERT INTO History values(?,?,?,?,?,?,?,?,?,?,?)",data)
    cursor.execute("Delete from Trek where TrekId=?",(TrekId,))
    conn.commit()
    conn.close()
    flash("Deleted The Trek","success")
    return redirect("/adminTreks")

@app.route("/searchTrek/<x>/<int:y>",methods=["GET","POST"])
def searchTrek(x,y):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    if(y==1):
        cursor.execute("SELECT * FROM Trek WHERE TrekName LIKE ?", (f"%{x}%",))
        treks=cursor.fetchall()
        conn.close()
        return render_template("adminTreks.html", treks=treks)
    else:
        cursor.execute("Select * from Trek where TrekId=?",(x,))
        treks=cursor.fetchall()
        conn.close()
        return render_template("adminTreks.html", treks=treks)

@app.route("/adminTrekkers", methods=["GET","POST"])
def adminTrekkers():
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    if(request.method=="POST"):
        NameorId=request.form.get("NameorId")
        if(NameorId):
            x=""
            y=1
            try:
                x=int(NameorId)
                y=0
            except ValueError:
                x=str(NameorId)
            conn.close()
            return redirect(url_for("searchTrekker",x=x,y=y))
        else:
            conn.close()
            flash("Please search after putting values", "warning")
            return redirect(url_for("adminTrekkers"))
    cursor.execute("Select * from User where UserRole='Trekker'")
    users=cursor.fetchall()
    conn.close()
    return render_template("adminTrekkers.html",users=users)
    
@app.route("/searchUser/<x>/<int:y>",methods=["GET","POST"])
def searchTrekker(x,y):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    if(y==1):
        cursor.execute("SELECT * FROM User WHERE FullName LIKE ? AND UserRole='Trekker'", (f"%{x}%",))
        users=cursor.fetchall()
        conn.close()
        return render_template("adminTrekkers.html",users=users)
    else:
        cursor.execute("Select * from User where UserId=? and UserRole='Trekker'",(x,))
        users=cursor.fetchall()
        conn.close()
        return render_template("adminTrekkers.html",users=users)
    

@app.route("/blacklist/<int:UserId>")
def blacklist(UserId):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("SELECT TrekId from Booking where UserId=?",(UserId,))
    data=cursor.fetchall()
    for trek in data:
        cursor.execute("Update Trek set Participants=Participants-1 where TrekId=?",(trek[0],))
        cursor.execute("Select Participants from Trek where TrekId=?",(trek[0],))
        p=cursor.fetchone()[0]
        if(p<0):
            cursor.execute("Update Trek set Participants=0 where TrekId=?",(trek[0],))
    cursor.execute("Delete from User where UserId=? and UserRole='Trekker'",(UserId,))
    conn.commit()
    conn.close()
    return redirect("/adminTrekkers")


@app.route("/adminStaff", methods=["GET","POST"])
def adminStaff():
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    if(request.method=="POST"):
        NameorId=request.form.get("NameorId")
        if(NameorId):
            x=""
            y=1
            try:
                x=int(NameorId)
                y=0
            except ValueError:
                x=str(NameorId)
            conn.close()
            return redirect(url_for("searchStaff",x=x,y=y))
        else:
            conn.close()
            flash("Please search after putting values", "warning")
            return redirect(url_for("adminStaff"))
    cursor.execute("Select * from User where UserRole='Staff'")
    staffs=cursor.fetchall()
    cursor.execute("Select * from StaffReq")
    reqstaffs=cursor.fetchall()
    conn.close()
    return render_template("adminStaff.html",staffs=staffs,reqstaffs=reqstaffs)
    
@app.route("/searchStaff/<x>/<int:y>",methods=["GET","POST"])
def searchStaff(x,y):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    if(y==1):
        cursor.execute("Select * from User where FullName LIKE ? and UserRole='Staff'",(f"%{x}%",))
        staffs=cursor.fetchall()
        cursor.execute("Select * from StaffReq")
        reqstaffs=cursor.fetchall()
        conn.close()
        return render_template("adminStaff.html", staffs=staffs, reqstaffs=reqstaffs)
    else:
        cursor.execute("Select * from User where UserId=? and UserRole='Staff'",(x,))
        staffs=cursor.fetchall()
        cursor.execute("Select * from StaffReq")
        reqstaffs=cursor.fetchall()
        conn.close()
        return render_template("adminStaff.html", staffs=staffs, reqstaffs=reqstaffs)
    

@app.route("/blacklistS/<int:UserId>")
def blacklistS(UserId):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("Select t.TrekId,t.TrekName from Trek t, Booking b where t.StaffId=? and t.TrekId=b.TrekId",(UserId,))
    treks=cursor.fetchone()
    if(treks):
        conn.close()
        return redirect(url_for("replaceStaff",StaffId=UserId))
    cursor.execute("Update Trek set StaffId=Null where StaffId=?",(UserId,))
    cursor.execute("Delete from User where UserId=? and UserRole='Staff'",(UserId,))
    conn.commit()
    conn.close()
    return redirect("/adminStaff")

@app.route("/replaceStaff/<int:StaffId>", methods=["GET","POST"])
def replaceStaff(StaffId):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    if(request.method=="POST"):
        cursor.execute("Select DISTINCT t.TrekId from Trek t, Booking b where t.StaffId=? and t.TrekId=b.TrekId",(StaffId,))
        treks=cursor.fetchall()
        count=1
        for trek in treks:
            staffId=request.form.get(f"StaffId{count}")
            count+=1
            cursor.execute("Select UserId from User where UserId=? and UserRole='Staff'",(staffId,))
            if not cursor.fetchone():
                conn.close()
                flash("Invalid staffId was tried to be assigned.")
                return redirect(url_for("replaceStaff",StaffId=StaffId))
            cursor.execute("Update Trek set StaffId=? where TrekId=?",(staffId,trek[0]))
            conn.commit()
        cursor.execute("DELETE FROM User WHERE UserId=? AND UserRole='Staff'",(StaffId,))
        conn.close()
        flash("Treks were updated","success")
        return redirect(url_for("adminStaff"))     
    cursor.execute("Select UserId,Fullname from User where UserRole='Staff' and UserId!=?",(StaffId,))
    staffs=cursor.fetchall()
    cursor.execute("Select DISTINCT t.TrekId,t.TrekName from Trek t, Booking b where t.StaffId=? and t.TrekId=b.TrekId",(StaffId,))
    treks=cursor.fetchall()
    conn.close()
    flash("The removed staff alredy have some assigned treks with booking.","message")
    return render_template("replaceStaff.html",treks=treks,staffs=staffs,sId=StaffId)

@app.route("/approve/<int:ReqId>",methods=["GET","POST"])
def approve(ReqId):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM StaffReq where ReqId=?",(ReqId,))
    staff=cursor.fetchone()
    if staff:
        cursor.execute("Insert into User (UserId,FullName,UserEmail,UserPassword,UserRole,Contact) values(?,?,?,?,'Staff',?)", (None, staff[1], staff[2], staff[3], staff[4]))
        cursor.execute("Delete from StaffReq where ReqId=?",(ReqId,))
        conn.commit()
    conn.close()
    return redirect("/adminStaff")

@app.route("/reject/<int:ReqId>",methods=["GET","POST"])
def reject(ReqId):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM StaffReq where ReqId=?",(ReqId,))
    staff=cursor.fetchone()
    if staff:
        cursor.execute("Delete from StaffReq where ReqId=?",(ReqId,))
        conn.commit()
    conn.close()
    return redirect("/adminStaff")

@app.route("/adminBookings", methods=["GET","POST"])
def adminBooking():
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    if(request.method=="POST"):
        NameorId=request.form.get("NameorId")
        SearchBy=request.form.get("SearchBy")
        if(NameorId):
            x=""
            y=1
            try:
                x=int(NameorId)
                y=0
            except ValueError:
                x=str(NameorId)
            conn.close()
            return redirect(url_for("searchBooking",x=x,y=y,s=SearchBy))
        else:
            conn.close()
            flash("Please search after putting values", "warning")
            return redirect(url_for("adminBooking"))

    cursor.execute("""SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b
      JOIN Trek t ON b.TrekId=t.TrekId 
      JOIN User u ON b.UserId=u.UserId LEFT JOIN User s ON t.StaffId=s.UserId ORDER BY BookingStatus""")
    bookings=cursor.fetchall() 
    conn.close()
    return render_template("adminBookings.html",bookings=bookings)
    
@app.route("/searchBooking/<x>/<int:y>/<string:s>",methods=["GET","POST"])
def searchBooking(x,y,s):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    if(s=="BookingId"):
        cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId=t.TrekId JOIN User u ON b.UserId=u.UserId LEFT JOIN User s ON t.StaffId=s.UserId WHERE b.BookingId=? ORDER BY BookingStatus", (x,))
        bookings=cursor.fetchall()
        conn.close()
        return render_template("adminBookings.html",bookings=bookings)
    elif(s=="TrekIdorName"):
        if(y==0):
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId=t.TrekId JOIN User u ON b.UserId=u.UserId LEFT JOIN User s ON t.StaffId=s.UserId WHERE b.TrekId=? ORDER BY BookingStatus", (x,))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html",bookings=bookings)
        else:
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId=t.TrekId JOIN User u ON b.UserId=u.UserId LEFT JOIN User s ON t.StaffId=s.UserId WHERE t.TrekName LIKE ? ORDER BY BookingStatus", (f"%{x}%",))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html", bookings=bookings) 
    elif(s=="StaffIdorName"):
        if(y==0):
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId=t.TrekId JOIN User u ON b.UserId=u.UserId LEFT JOIN User s ON t.StaffId=s.UserId WHERE s.UserId=? ORDER BY BookingStatus", (x,))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html",bookings=bookings)
        else:
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId=t.TrekId JOIN User u ON b.UserId=u.UserId LEFT JOIN User s ON t.StaffId=s.UserId WHERE s.FullName LIKE ? ORDER BY BookingStatus", (f"%{x}%",))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html",bookings=bookings)
    elif(s=="UserIdorName"):
        if(y==0):
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId=t.TrekId JOIN User u ON b.UserId=u.UserId LEFT JOIN User s ON t.StaffId=s.UserId WHERE u.UserId=? ORDER BY BookingStatus", (x,))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html",bookings=bookings)
        else:
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId=t.TrekId JOIN User u ON b.UserId=u.UserId LEFT JOIN User s ON t.StaffId=s.UserId WHERE u.FullName LIKE ? ORDER BY BookingStatus", (f"%{x}%",))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html",bookings=bookings)
    else:
        conn.close()
        return "ERROR in SearchBy"

@app.route("/adminHistory",methods=["GET","POST"])
def adminHistory():
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    if(request.method=="POST"):
        NameorId=request.form.get("NameorId")
        SearchBy=request.form.get("SearchBy")
        if(NameorId):
            x=""
            y=1
            try:
                x=int(NameorId)
                y=0
            except ValueError:
                x=str(NameorId)
            conn.close()
            return redirect(url_for("searchHistory",x=x,y=y,s=SearchBy))
        else:
            conn.close()
            flash("Please search after putting values", "warning")
            return redirect(url_for("adminHistory"))
    cursor.execute("SELECT * from History")
    trekkings=cursor.fetchall()
    conn.close()
    return render_template("adminHistory.html",trekkings=trekkings)     

@app.route("/searchHistory/<x>/<int:y>/<string:s>",methods=["GET","POST"])
def searchHistory(x,y,s):
    response=checkAdmin()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    if(s=="BookingId"):
        cursor.execute("Select * from History where BookingId=?",(x,))
        trekkings=cursor.fetchall()
        conn.close()
        return render_template("adminHistory.html",trekkings=trekkings)
    elif(s=="TrekIdorName"):
        if(y==0):
            cursor.execute("Select * from History where TrekId=?",(x,))
            trekkings=cursor.fetchall()
            conn.close()
            return render_template("adminHistory.html",trekkings=trekkings)
        else:
            cursor.execute("Select * from History where TrekName like ?",(f"%{x}%",))
            trekkings=cursor.fetchall()
            conn.close()
            return render_template("adminHistory.html",trekkings=trekkings)
    elif(s=="StaffIdorName"):
        if(y==0):
            cursor.execute("Select * from History where StaffId=?",(x,))
            trekkings=cursor.fetchall()
            conn.close()
            return render_template("adminHistory.html",trekkings=trekkings)
        else:
            cursor.execute("Select * from History where StaffName like ?",(f"%{x}%",))
            trekkings=cursor.fetchall()
            conn.close()
            return render_template("adminHistory.html",trekkings=trekkings)
    elif(s=="UserIdorName"):
        if(y==0):
            cursor.execute("Select * from History where TrekkerId=?",(x,))
            trekkings=cursor.fetchall()
            conn.close()
            return render_template("adminHistory.html",trekkings=trekkings)
        else:
            cursor.execute("Select * from History where TrekkerName like ?",(f"%{x}%",))
            trekkings=cursor.fetchall()
            conn.close()
            return render_template("adminHistory.html",trekkings=trekkings)
    else:
        conn.close()
        return "ERROR in SearchBy"

@app.route('/staffDashboard')
def staffDashboard():
    response=checkStaff()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    Id=session.get("UserId")
    cursor.execute("Select * from User where UserId=?",(Id,))  
    UserInfo=cursor.fetchone()
    cursor.execute("Select TrekId, TrekName, Location, Participants, Slot, Status from Trek where StaffId=? Limit 3",(Id,))
    aTreks=cursor.fetchall()
    cursor.execute("Select COUNT(TrekId) from Trek where StaffId=?",(Id,))
    a=cursor.fetchone()[0]
    cursor.execute("Select Count(u.UserId) from Trek t, User u, Booking b where u.UserId=b.UserId and t.TrekId=b.TrekId and t.StaffId=?",(Id,))
    p=cursor.fetchone()[0]
    cursor.execute("Select COUNT(DISTINCT TrekId) from History where StaffId=?",(Id,))
    c=cursor.fetchone()[0]
    conn.close()
    return render_template("staffDashboard.html",UserInfo=UserInfo,aTreks=aTreks,a=a,p=p,c=c) 

@app.route("/staffProfile")
def staffProfile():
    response=checkStaff()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    staffId=session.get("UserId")
    cursor.execute("Select UserId, Fullname, UserEmail, Contact from User where UserId=?",(staffId,))
    Staff=cursor.fetchone()
    cursor.execute("Select COUNT(DISTINCT TrekId) from History where StaffId=?",(staffId,))
    c=cursor.fetchone()[0]
    conn.close()
    return render_template("staffProfile.html",Staff=Staff,c=c)

@app.route("/assignedTreks")
def assignedTreks():
    response=checkStaff()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    staffId=session.get("UserId")
    cursor.execute("Select * from Trek where StaffId=?",(staffId,))
    aTreks=cursor.fetchall()
    conn.close()
    return render_template("assignedTreks.html",aTreks=aTreks)


@app.route("/staffTrekkers")
def staffTrekkers():
    response=checkStaff()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    staffId=session.get("UserId")
    cursor.execute("""Select t.TrekId,u.UserId, TrekName, FullName, UserEmail, Contact from Trek t, Booking b, User u 
        where u.UserId=b.UserId and b.TrekId=t.TrekId and t.StaffId=? and b.BookingStatus='Booked'""",(staffId,))
    Trekkers=cursor.fetchall()
    cursor.execute("""Select DISTINCT t.TrekId, TrekName from Trek t, Booking b, User u 
        where u.UserId=b.UserId and b.TrekId=t.TrekId and t.StaffId=? and b.BookingStatus='Booked'""",(staffId,))
    aTreks=cursor.fetchall()
    conn.close()
    return render_template("staffTrekkers.html",aTreks=aTreks,Trekkers=Trekkers)

@app.route("/editStaffProfile", methods=["GET","POST"])
def editStaffProfile():
    response=checkStaff()
    if response:
        return response
    if(request.method=="POST"):
        conn=sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor=conn.cursor()
        name=request.form.get("name")
        email=request.form.get("email")
        contact=request.form.get("contact")
        staffId=session.get("UserId")
        cursor.execute("SELECT UserId from User where UserEmail=? and UserId!=?",(email,staffId))
        row=cursor.fetchone()
        if row:
            flash("This email is already in use.","error")
            conn.close()
            return redirect("/editStaffProfile")
        cursor.execute("Update User set FullName=?, UserEmail=?,Contact=? where UserId=?",(name,email,contact,staffId))
        conn.commit()
        conn.close()
        return redirect(url_for("staffProfile"))
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    staffId=session.get("UserId")
    cursor.execute("Select UserId, Fullname, UserEmail, Contact from User where UserId=?",(staffId,))
    Staff=cursor.fetchone()
    conn.close()
    return render_template("editStaffProfile.html",Staff=Staff)

@app.route("/manageTrekS/<int:trekId>", methods=["GET","POST"])
def manageTrekS(trekId):
    response=checkStaff()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("Select StaffId from Trek where TrekId=?",(trekId,))
    row=cursor.fetchone()
    if(not row):
        conn.close()
        return "Trek not found",404
    StaffId=row[0]
    if(StaffId!=session.get("UserId")):
        conn.close()
        return render_template("unauthorized.html")
    if(request.method=="POST"):
        try:
            Slot=int(request.form.get("Slot"))
        except (TypeError,ValueError):
            conn.close()
            flash("Slot must be a number","error")
            return redirect(url_for("manageTrekS",trekId=trekId))
        if(Slot<=0):
            conn.close()
            flash("Slots should be greater than 0")
            return redirect(url_for("manageTrekS",trekId=trekId))
        Status=request.form.get("Status")
        cursor.execute("Select Participants from Trek where TrekId=?",(trekId,))
        p=cursor.fetchone()[0]
        if(Slot<p):
            conn.close()
            flash("Slots can not be less than bookings already booked","error")
            return redirect(url_for("manageTrekS",trekId=trekId))
        cursor.execute("Update Trek set Slot=?, Status=? where TrekId=?",(Slot,Status,trekId))
        conn.commit()
        conn.close()
        return redirect(url_for("assignedTreks"))

    cursor.execute("Select * from Trek where TrekId=?",(trekId,))
    trek=cursor.fetchone()
    conn.close()
    return render_template("manageTrekS.html",trek=trek)

# @app.route("/trekDetailS/<int:trekId>")
# def trekDetailS(trekId):
#     response=checkStaff()
#     if response:
#         return response
#     conn=sqlite3.connect("TrekManagement.db")
#     conn.execute("PRAGMA foreign_keys=ON;")
#     cursor=conn.cursor()
#     cursor.execute("Select StaffId from Trek where TrekId=?",(trekId,))
#     StaffId=cursor.fetchone()[0]
#     if(StaffId!=session.get("UserId")):
#         conn.close()
#         return render_template("unauthorized.html")
#     cursor.execute("Select * from Trek where TrekId=?",(trekId,))
#     trek=cursor.fetchone()
#     conn.close()
#     return render_template("trekDetailS.html",trek=trek)

@app.route("/markOngoing/<int:trekId>")
def markOngoing(trekId):
    response=checkStaff()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("Select StaffId,Status from Trek where TrekId=?",(trekId,))
    row=cursor.fetchone()
    if(not row):
        conn.close()
        return "trek does not exist",404
    if(row[1]!="Open"):
        conn.close()
        flash("Only an open trek can be marked as ongoing","warning")
        return redirect(url_for("manageTrekS",trekId=trekId))
    StaffId=row[0]
    if(StaffId!=session.get("UserId")):
        conn.close()
        return render_template("unauthorized.html")
    cursor.execute("Update Trek set Status='Ongoing' where trekId=?",(trekId,))
    conn.commit()
    cursor.execute("Select * from Trek where trekId=?",(trekId,))
    trek=cursor.fetchone()
    conn.close()
    return render_template("manageTrekS.html",trek=trek)

@app.route("/markCompleted/<int:trekId>")
def markCompleted(trekId):
    response=checkStaff()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("Select StaffId,Status from Trek where TrekId=?",(trekId,))
    row=cursor.fetchone()
    if(not row):
        conn.close()
        return "trek does not exist",404
    StaffId=row[0]
    if(StaffId!=session.get("UserId")):
        conn.close()
        return render_template("unauthorized.html")
    if(row[1]!="Ongoing"):
        conn.close()
        flash("You can not mark this trek as completed.It was not marked on going","error")
        return redirect(url_for("manageTrekS",trekId=trekId))
    staffId=session.get("UserId")
    cursor.execute("""Select BookingId, u.UserId, u.FullName, t.TrekId, t.TrekName, t.StaffId,s.FullName,t.StartDate,t.EndDate,b.BookingDate
        FROM Trek t, Booking b, User u LEFT JOIN User s on s.UserId=t.StaffId
        where t.TrekId=b.TrekId and b.UserId=u.UserId and t.TrekId=? and t.StaffId=?""",(trekId,staffId))
    data=cursor.fetchall()
    for rec in data:
        cursor.execute("INSERT INTO History(BookingId, TrekkerId,TrekkerName, TrekId, TrekName, StaffId, StaffName,TrekStart ,TrekEnd,BookingDate,Status) values(?,?,?,?,?,?,?,?,?,?,'Completed')", rec)
    cursor.execute("Delete from Trek where TrekId=?",(trekId,))
    # for booking in data:
    #     cursor.execute("Delete from Booking where BookingId=?",(booking[0],))
    conn.commit()
    conn.close()
    return redirect(url_for("assignedTreks"))

@app.route("/removeParticipant/<int:trekkerId>/<int:trekId>")
def removeParticipant(trekkerId,trekId):
    response=checkStaff()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("Select StaffId from Trek where TrekId=?",(trekId,))
    row=cursor.fetchone()
    if(not row):
        conn.close()
        return "trek does not exist",404
    StaffId=row[0]
    if(StaffId!=session.get("UserId")):
        conn.close()
        return render_template("unauthorized.html")
    cursor.execute("SELECT BookingId from Booking where UserId=? and TrekId=?",(trekkerId,trekId))
    row=cursor.fetchone()
    if not row:
        conn.close()
        return "Booking Not Found",404
    BookingId=row[0]
    cursor.execute("SELECT BookingId,u.UserId,u.Fullname,t.TrekId,t.TrekName,t.StaffId,s.Fullname,t.StartDate,t.EndDate,b.BookingDate,'Revoked' from Booking b Join Trek t on b.Trekid=t.TrekId Join User u on b.UserId=u.UserId LEFT Join User s on t.StaffId=s.UserId where b.BookingId=?",(BookingId,))
    data=cursor.fetchone()
    if not data:
        conn.close()
        flash("No such booking was found","error")
        return redirect(url_for("staffTrekkers"))
    cursor.execute("INSERT INTO History values(?,?,?,?,?,?,?,?,?,?,?)",data)
    cursor.execute("DELETE from Booking where TrekId=? and UserId=?",(trekId,trekkerId))
    cursor.execute("Update Trek set Participants=Participants-1 where trekId=?",(trekId,))
    conn.commit()
    conn.close()
    return redirect(url_for("staffTrekkers"))

@app.route('/trekkerDashboard')
def trekkerDashboard():
    response=checkTrekker()
    if response:
        return response
    session["val"]=0
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    cursor.execute("SELECT TrekId, TrekName,Location,Difficulty,Duration_HRS,Slot-Participants from Trek where Status='Open' and Slot-Participants>0 LIMIT 5")
    aTreks=cursor.fetchall()
    Id=session.get("UserId")
    cursor.execute("Select * from User where UserId=?",(Id,))  
    UserInfo=cursor.fetchone()
    conn.close()
    return render_template("trekkerDashboard.html",aTreks=aTreks,userInfo=UserInfo)

@app.route('/trekkerProfile')
def trekkerProfile():
    response=checkTrekker()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    Id=session.get("UserId")
    cursor.execute("Select UserId,FullName,UserEmail,Contact from User where UserId=?",(Id,))  
    Trekker=cursor.fetchone()
    cursor.execute("Select COUNT(TrekId) from History where TrekkerId=?",(Id,))
    c=cursor.fetchone()[0]
    conn.close()
    return render_template("trekkerProfile.html",c=c,Trekker=Trekker)

@app.route("/editTrekkerProfile", methods=["GET","POST"])
def editTrekkerProfile():
    response=checkTrekker()
    if response:
        return response
    Id=session.get("UserId")
    if(request.method=="POST"):
        name=request.form.get("name")
        email=request.form.get("email")
        contact=request.form.get("contact")
        conn=sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor=conn.cursor()
        cursor.execute("SELECT UserId from User where UserEmail=? and UserId!=?",(email,Id))
        row=cursor.fetchone()
        if row:
            flash("This email is already in use.","error")
            conn.close()
            return redirect("/editTrekkerProfile")
        Id=session.get("UserId")
        cursor.execute("UPDATE User set FullName=?, UserEmail=?, contact=? where UserId=?",(name,email,contact,Id))
        conn.commit()
        conn.close()
        return redirect(url_for("trekkerProfile"))
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    
    cursor.execute("Select UserId,FullName,UserEmail,Contact from User where UserId=?",(Id,))
    Trekker=cursor.fetchone()
    conn.close()
    return render_template("editTrekkerProfile.html",Trekker=Trekker)

@app.route("/trekkerTreks", methods=["GET","POST"])
def trekkerTreks():
    response=checkTrekker()
    if response:
        return response
    if(request.method=="POST"):
        location=request.form.get("Location")
        difficulty=request.form.get("Difficulty")
        Id=session.get("UserId")
        if difficulty=="Any":
            difficulty=None        
        if(not location and not difficulty):
            flash("Please put the values first","warning")
            return redirect("/trekkerTreks")
        conn=sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor=conn.cursor()
        if(not location):
            cursor.execute("Select TrekId, TrekName,Difficulty,Location,Duration_Hrs,Slot-Participants,StartDate,Status,u.Fullname,u.Contact from Trek t, User u where Status='Open' and Slot-Participants>0 and u.UserId=t.StaffId and not exists(Select 1 from Booking b where t.TrekId=b.TrekId and UserId=?) and Difficulty=?",(Id,difficulty))
        elif(not difficulty):
            cursor.execute("Select TrekId, TrekName,Difficulty,Location,Duration_Hrs,Slot-Participants,StartDate,Status,u.Fullname,u.Contact from Trek t, User u where Status='Open' and Slot-Participants>0 and u.UserId=t.StaffId and not exists(Select 1 from Booking b where t.TrekId=b.TrekId and UserId=?) and Location like ?",(Id,f"%{location}%"))
        else:
            cursor.execute("Select TrekId, TrekName,Difficulty,Location,Duration_Hrs,Slot-Participants,StartDate,Status,u.Fullname,u.Contact from Trek t, User u where Status='Open' and Slot-Participants>0 and u.UserId=t.StaffId and not exists(Select 1 from Booking b where t.TrekId=b.TrekId and UserId=?) and Difficulty=? and Location like ?",(Id,difficulty,f"%{location}%"))
        aTreks=cursor.fetchall()
        conn.close()
        return render_template("trekkerTreks.html",aTreks=aTreks)


    session["val"]=2
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    Id=session.get("UserId")
    cursor.execute("Select TrekId, TrekName,Difficulty,Location,Duration_Hrs,Slot-Participants,StartDate,Status,u.Fullname,u.Contact from Trek t, User u where Status='Open' and Slot-Participants>0 and u.UserId=t.StaffId and not exists(Select 1 from Booking b where t.TrekId=b.TrekId and UserId=?)",(Id,))
    aTreks=cursor.fetchall()
    conn.close()
    return render_template("trekkerTreks.html",aTreks=aTreks)

# @app.route("/trekDetailT/<int:TrekId>")
# def trekDetailT(TrekId):
#     response=checkTrekker()
#     if response:
#         return response
#     session["val"]=3
#     conn=sqlite3.connect("TrekManagement.db")
#     conn.execute("PRAGMA foreign_keys=ON;")
#     cursor=conn.cursor()
#     cursor.execute("Select TrekId,TrekName,Difficulty,Location,Duration_HRS,StartDate,EndDate,Slot,u.FullName,Status,Contact from Trek t Left Join User u on t.StaffId=u.UserId where TrekId=?",(TrekId,))
#     trek=cursor.fetchone()
#     conn.close()
#     return render_template("trekDetailT.html",trek=trek)

@app.route("/bookTrek/<int:TrekId>", methods=["GET","POST"])
def bookTrek(TrekId):
    response=checkTrekker()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    Id=session.get("UserId")
    if(request.method=='POST'):
        cursor.execute("Select BookingId from Booking where UserId=? and TrekId=? and BookingStatus='Booked'",(Id,TrekId))
        if cursor.fetchone():
            flash("You have already booked this Trek","error")
            conn.close()
            return redirect(url_for("bookedTreks"))
        cursor.execute("Select Participants,Slot,Status from Trek where TrekId=?",(TrekId,))
        row=cursor.fetchone()
        if not row:
            conn.close()
            return "Trek Not found",404
        if row[2]!= "Open":
            conn.close()
            flash("This trek is not open for booking.","warning")
            return redirect(url_for("trekkerTreks"))
        p,s=row[0],row[1]
        if p>=s:
            flash("No slots available.","warning")
            conn.close()
            return redirect(url_for("trekkerTreks"))
        cursor.execute("INSERT into Booking(BookingId,UserId,TrekId,BookingStatus,BookingDate,PaymentStatus) values(?,?,?,?,?,?)",(None,Id,TrekId,'Booked',date.today(),'Done'))
        flash("Your Booking was Completed","success")
        cursor.execute("Update Trek set Participants=Participants+1 where TrekId=?",(TrekId,))
        conn.commit()
        conn.close()
        return redirect(url_for("bookedTreks"))
    conn.close()
    return render_template("bookTrek.html",TrekId=TrekId)

@app.route("/bookedTreks")
def bookedTreks():
    response=checkTrekker()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    Id=session.get("UserId")
    cursor.execute("SELECT BookingId,TrekName,BookingDate,StartDate,Duration_HRS,BookingStatus,PaymentStatus,EndDate,s.UserId,s.FullName,s.Contact,Difficulty,Location from Trek t,Booking b Left Join User s on s.UserId=t.StaffId where b.TrekId=t.TrekId and b.UserId=?",(Id,))
    bookings=cursor.fetchall()
    conn.close()
    return render_template("bookedTreks.html",bookings=bookings)

@app.route("/cancelBooking/<int:BookingId>")
def cancelBooking(BookingId):
    response=checkTrekker()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    Id=session.get("UserId")
    cursor.execute("SELECT TrekId,BookingStatus FROM Booking WHERE BookingId=? AND UserId=?",(BookingId, Id))
    row=cursor.fetchone()
    if not row:
        conn.close()
        return render_template("unauthorized.html")
    if row[1] != "Booked":
        conn.close()
        return "This booking cannot be cancelled"
    
    cursor.execute("Select b.TrekId,t.StartDate,t.Status from Booking b Join Trek t on t.TrekId=b.TrekId where BookingId=?",(BookingId,))
    row=cursor.fetchone()
    if(row[1].strip()<=str(date.today()) or row[2]!="Open"):
        conn.close()
        return "You can not cancel booking now"

    if row:
        TrekId=row[0]
        cursor.execute("SELECT BookingId,u.UserId,u.Fullname,t.TrekId,t.TrekName,t.StaffId,s.Fullname,t.StartDate,t.EndDate,b.BookingDate,'Cancelled' from Booking b Join Trek t on b.Trekid=t.TrekId Join User u on b.UserId=u.UserId LEFT Join User s on t.StaffId=s.UserId where b.BookingId=?",(BookingId,))
        data=cursor.fetchone()
        cursor.execute("INSERT INTO History values(?,?,?,?,?,?,?,?,?,?,?)",data)
        cursor.execute("Delete from Booking where BookingId=?",(BookingId,))
        cursor.execute("Update Trek set Participants=Participants-1 where TrekId=?",(TrekId,)) 
        conn.commit()
    conn.close()
    return redirect(url_for("bookedTreks"))


@app.route("/trekkerHistory")
def trekkerHistory():
    response=checkTrekker()
    if response:
        return response
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor=conn.cursor()
    Id=session.get("UserId")
    cursor.execute("Select BookingId, TrekName, BookingDate,TrekStart,TrekEnd,Status from History where TrekkerId=?",(Id,))
    trekkings=cursor.fetchall()
    conn.close()
    return render_template("trekkerHistory.html",trekkings=trekkings)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)