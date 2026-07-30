from flask import Flask, render_template, request, redirect, url_for,flash,session
import sqlite3 

app=Flask(__name__)
app.secret_key="trekker"


@app.route('/',methods=["GET","POST"])
def index():
    if "UserId" in session:
        conn = sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor=conn.cursor()
        Id=session.get("UserId")
        cursor.execute("Select UserRole from User where UserId=?",(Id,))
        Role=cursor.fetchone()[0]
        conn.close()
        if(Role):
            if(Role=="Admin"):
                return redirect(url_for("adminDashboard"))
            elif(Role=="Staff"):
                return redirect(url_for("staffDashboard"))
            else:
                return redirect(url_for("userDashboard"))
        else:
            flash("No Data found in database", "error")
            return redirect(url_for("login"))
    else:
        return redirect(url_for("login"))
        

@app.route('/login',methods=["GET","POST"])
def login():
    if(request.method=="POST"):
        conn = sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor=conn.cursor()
        username=request.form.get("Username")
        password=request.form.get("Password")
        cursor.execute("Select * from User where UserEmail=? AND UserPassword=?",(username,password))
        userInfo=cursor.fetchone()
        conn.close()
        if(userInfo):
            session['UserId']=userInfo[0]
            if(userInfo[4]=="Admin"):
                return redirect(url_for("adminDashboard"))
            elif(userInfo[4]=="Staff"):
                return redirect(url_for("staffDashboard"))
            else:
                return redirect(url_for("userDashboard"))
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for("login"))
        
    return render_template("login.html")

@app.route('/register',methods=["GET","POST"])
def register():
    if(request.method=="POST"):
        conn = sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor=conn.cursor()
        name=request.form.get("Fullname")
        email=request.form.get("Email")
        password=request.form.get("Password")
        password2=request.form.get("Password2")
        contact=request.form.get("Contact")
        role=request.form.get("Role")
        if(password!=password2):
            flash("Please enter same password for confirmation","warning")
            conn.close()
            return redirect('/register')
        if(role=="Trekker"):
            cursor.execute("Insert into User (UserId,FullName,UserEmail,UserPassword,UserRole,Contact) values(?,?,?,?,?,?)",(None,name,email,password,role,contact))
            conn.commit()
            conn.close()
            flash("Successfully registered as Trekker","success")
            return redirect('/login')
        else:
            cursor.execute("Insert into StaffReq (ReqId,Name,Email,Password,Contact) values(?,?,?,?,?)",(None,name,email,password,contact))
            conn.commit()
            conn.close()
            flash("Request Sent to Admin, You can login once admin approves","success")
            return redirect('/')
        
    return render_template("register.html")

@app.route('/adminDashboard')
def adminDashboard():
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
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
    Bookings=cursor.fetchall()  
    Id=session.get("UserId")
    cursor.execute("Select * from User where UserId=?",(Id,))  
    UserInfo=cursor.fetchone()
    conn.close()
    return render_template("adminDashboard.html",TotalTreks=TotalTreks,TotalUsers=TotalUsers,TotalStaff=TotalStaff,TotalBookings=TotalBookings,Bookings=Bookings,UserInfo=UserInfo)

@app.route('/addTrek',methods=["GET","POST"])
def addTrek():
    if(request.method=="POST"):
        conn=sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor=conn.cursor()
        TrekName=request.form.get("Trekname")
        TrekDifficulty=request.form.get("Difficulty")
        TrekLocation=request.form.get("Location")
        TrekDuration=request.form.get("Duration")
        TrekS=request.form.get("sDate")
        TrekE=request.form.get("eDate")
        TrekSlot=request.form.get("Slot")
        TrekStaff=request.form.get("StaffId") or None
        cursor.execute("INSERT INTO Trek(TrekId,TrekName,Difficulty,Location,Duration_HRS,StartDate,EndDate,Slot,StaffId,Status) VALUES(?,?,?,?,?,?,?,?,?,'Open')",(None,TrekName,TrekDifficulty,TrekLocation,TrekDuration,TrekS,TrekE,TrekSlot,TrekStaff))
        conn.commit()
        conn.close()
        return redirect("/adminTreks")
    return render_template("addTrek.html")

@app.route("/adminTreks", methods=["GET","POST"])
def adminTreks():
    if(request.method=="POST"):
        NameorId=request.form.get("NameorId")
        if(NameorId):
            x=""
            y=1
            try:
                x=int(NameorId)
                y=0
            except:
                x=str(NameorId)
            return redirect(url_for("searchTrek",x=x,y=y))
        else:
            flash("Please search after putting values", "error")
            return redirect(url_for("adminTreks"))

    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    cursor.execute("Select * from Trek")
    treks=cursor.fetchall()
    conn.close()
    return render_template("adminTreks.html",treks=treks)

@app.route("/editTrek/<int:TrekId>",methods=["GET","POST"])
def editTrek(TrekId):
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    if(request.method=="POST"):
        TrekName=request.form.get("Trekname")
        TrekDifficulty=request.form.get("Difficulty")
        TrekLocation=request.form.get("Location")
        TrekDuration=request.form.get("Duration")
        TrekS=request.form.get("sDate")
        TrekE=request.form.get("eDate")
        TrekSlot=request.form.get("Slot")
        TrekStaff=request.form.get("StaffId") or None
        TrekStatus=request.form.get("Status")
        cursor.execute("""UPDATE Trek SET TrekName=?, Difficulty=?, Location=?, Duration_HRS=?, StartDate=?, EndDate=?, Slot=?, StaffId=?, Status=? WHERE TrekId=?""", (
            TrekName,TrekDifficulty,TrekLocation,TrekDuration,TrekS,TrekE,TrekSlot,TrekStaff,TrekStatus,TrekId))
        conn.commit()
        conn.close()
        return redirect("/adminTreks")
    
    cursor.execute("Select * from Trek where TrekId=?",(TrekId,))
    trek=cursor.fetchone()
    return render_template("editTrek.html",trek=trek)

@app.route("/removeTrek/<int:TrekId>")
def removeTrek(TrekId):
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    cursor.execute("Delete from Trek where TrekId=?",(TrekId,))
    conn.commit()
    conn.close()
    return redirect("/adminTreks")

@app.route("/searchTrek/<x>/<int:y>",methods=["GET","POST"])
def searchTrek(x,y):
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    if(y==1):
        cursor.execute("SELECT * FROM Trek WHERE TrekName LIKE ?", (f"{x}%",))
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
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    if(request.method=="POST"):
        NameorId=request.form.get("NameorId")
        if(NameorId):
            x=""
            y=1
            try:
                x=int(NameorId)
                y=0
            except:
                x=str(NameorId)
            conn.close()
            return redirect(url_for("searchTrekker",x=x,y=y))
        else:
            conn.close()
            flash("Please search after putting values", "error")
            return redirect(url_for("adminTrekkers"))
    cursor.execute("Select * from User where UserRole='Trekker'")
    users=cursor.fetchall()
    conn.close()
    return render_template("adminTrekkers.html",users=users)
    
@app.route("/searchUser/<x>/<int:y>",methods=["GET","POST"])
def searchTrekker(x,y):
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    if(y==1):
        cursor.execute("SELECT * FROM User WHERE FullName LIKE ? AND UserRole = 'Trekker'", (f"{x}%",))
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
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    cursor.execute("Delete from User where UserId=?",(UserId,))
    conn.commit()
    conn.close()
    return redirect("/adminTrekkers")


@app.route("/adminStaff", methods=["GET","POST"])
def adminStaff():
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    if(request.method=="POST"):
        NameorId=request.form.get("NameorId")
        if(NameorId):
            x=""
            y=1
            try:
                x=int(NameorId)
                y=0
            except:
                x=str(NameorId)
            conn.close()
            return redirect(url_for("searchStaff",x=x,y=y))
        else:
            conn.close()
            flash("Please search after putting values", "error")
            return redirect(url_for("adminStaff"))
    cursor.execute("Select * from User where UserRole='Staff'")
    staffs=cursor.fetchall()
    cursor.execute("Select * from StaffReq")
    reqstaffs=cursor.fetchall()
    conn.close()
    return render_template("adminStaff.html",staffs=staffs,reqstaffs=reqstaffs)
    
@app.route("/searchStaff/<x>/<int:y>",methods=["GET","POST"])
def searchStaff(x,y):
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    if(y==1):
        cursor.execute("Select * from User where FullName LIKE ? and UserRole='Staff'",(f"{x}%",))
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
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    cursor.execute("Delete from User where UserId=?",(UserId,))
    conn.commit()
    conn.close()
    return redirect("/adminStaff")

@app.route("/approve/<int:ReqId>",methods=["GET","POST"])
def approve(ReqId):
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
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
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
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
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
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
            except:
                x=str(NameorId)
            conn.close()
            return redirect(url_for("searchBooking",x=x,y=y,s=SearchBy))
        else:
            conn.close()
            flash("Please search after putting values", "error")
            return redirect(url_for("adminBooking"))

    cursor.execute("""SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b
      JOIN Trek t ON b.TrekId = t.TrekId 
      JOIN User u ON b.UserId = u.UserId LEFT JOIN User s ON t.StaffId = s.UserId ORDER BY BookingStatus""")
    bookings = cursor.fetchall() 
    conn.close()
    return render_template("adminBookings.html",bookings=bookings)
    
@app.route("/searchBooking/<x>/<int:y>/<string:s>",methods=["GET","POST"])
def searchBooking(x,y,s):
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    if(s=="BookingId"):
        cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId = t.TrekId JOIN User u ON b.UserId = u.UserId LEFT JOIN User s ON t.StaffId = s.UserId WHERE b.BookingId=? ORDER BY BookingStatus", (x,))
        bookings=cursor.fetchall()
        conn.close()
        return render_template("adminBookings.html",bookings=bookings)
    elif(s=="TrekIdorName"):
        if(y==0):
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId = t.TrekId JOIN User u ON b.UserId = u.UserId LEFT JOIN User s ON t.StaffId = s.UserId WHERE b.TrekId=? ORDER BY BookingStatus", (x,))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html",bookings=bookings)
        else:
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId = t.TrekId JOIN User u ON b.UserId = u.UserId LEFT JOIN User s ON t.StaffId = s.UserId WHERE t.TrekName LIKE ? ORDER BY BookingStatus", (f"{x}%",))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html", bookings=bookings) 
    elif(s=="StaffIdorName"):
        if(y==0):
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId = t.TrekId JOIN User u ON b.UserId = u.UserId LEFT JOIN User s ON t.StaffId = s.UserId WHERE s.UserId=? ORDER BY BookingStatus", (x,))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html",bookings=bookings)
        else:
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId = t.TrekId JOIN User u ON b.UserId = u.UserId LEFT JOIN User s ON t.StaffId = s.UserId WHERE s.FullName LIKE ? ORDER BY BookingStatus", (f"{x}%",))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html",bookings=bookings)
    elif(s=="UserIdorName"):
        if(y==0):
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId = t.TrekId JOIN User u ON b.UserId = u.UserId LEFT JOIN User s ON t.StaffId = s.UserId WHERE u.UserId=? ORDER BY BookingStatus", (x,))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html",bookings=bookings)
        else:
            cursor.execute("SELECT BookingId, b.TrekId, t.TrekName, s.UserId, s.FullName, u.UserId, u.FullName, BookingStatus FROM Booking b JOIN Trek t ON b.TrekId = t.TrekId JOIN User u ON b.UserId = u.UserId LEFT JOIN User s ON t.StaffId = s.UserId WHERE u.FullName LIKE ? ORDER BY BookingStatus", (f"{x}%",))
            bookings=cursor.fetchall()
            conn.close()
            return render_template("adminBookings.html",bookings=bookings)
    else:
        conn.close()
        return "ERROR in SearchBy"
    
# Staff Dashboard
@app.route('/staffDashboard')
def staffDashboard():
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    Id=session.get("UserId")
    cursor.execute("Select * from User where UserId=?",(Id,))  
    UserInfo=cursor.fetchone()
    cursor.execute("Select TrekId, TrekName, Location, Participants, Slot, Status from Trek where StaffId=?",(Id,))
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
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
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
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    staffId=session.get("UserId")
    cursor.execute("Select * from Trek where StaffId=?",(staffId,))
    aTreks=cursor.fetchall()
    conn.close()
    return render_template("assignedTreks.html",aTreks=aTreks)


@app.route("/staffTrekkers")
def staffTrekkers():
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    staffId=session.get("UserId")
    cursor.execute("""Select t.TrekId,u.UserId, TrekName, FullName, UserEmail, Contact from Trek t, Booking b, User u 
        where u.UserId=b.UserId and b.TrekId=t.TrekId and t.StaffId=?""",(staffId,))
    Trekkers=cursor.fetchall()
    cursor.execute("""Select DISTINCT t.TrekId, TrekName from Trek t, Booking b, User u 
        where u.UserId=b.UserId and b.TrekId=t.TrekId and t.StaffId=?""",(staffId,))
    aTreks=cursor.fetchall()
    return render_template("stafftrekkers.html",aTreks=aTreks,Trekkers=Trekkers)

@app.route("/editStaffProfile", methods=["GET","POST"])
def editStaffProfile():
    if(request.method=="POST"):
        conn=sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor=conn.cursor()
        name=request.form.get("name")
        email=request.form.get("email")
        contact=request.form.get("contact")
        staffId=session.get("UserId")
        cursor.execute("Update User set FullName=?, UserEmail=?,Contact=? where UserId=?",(name,email,contact,staffId))
        conn.commit()
        conn.close()
        return redirect(url_for("staffProfile"))
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    staffId=session.get("UserId")
    cursor.execute("Select UserId, Fullname, UserEmail, Contact from User where UserId=?",(staffId,))
    Staff=cursor.fetchone()
    return render_template("editStaffProfile.html",Staff=Staff)

@app.route("/manageTrekS/<int:trekId>", methods=["GET","POST"])
def manageTrekS(trekId):
    if(request.method=="POST"):
        Slot=request.form.get("Slot")
        Status=request.form.get("Status")
        conn=sqlite3.connect("TrekManagement.db")
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor=conn.cursor()
        cursor.execute("Update Trek set Slot=?, Status=? where TrekId=?",(Slot,Status,trekId))
        conn.commit()
        conn.close()
        return redirect(url_for("assignedTreks"))
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    cursor.execute("Select * from Trek where TrekId=?",(trekId,))
    trek=cursor.fetchone()
    conn.close()
    return render_template("manageTrekS.html",trek=trek)

@app.route("/trekDetailS/<int:trekId>")
def trekDeatilS(trekId):
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    cursor.execute("Select * from Trek where TrekId=?",(trekId,))
    trek=cursor.fetchone()
    conn.close()
    return render_template("trekDetailS.html",trek=trek)

@app.route("/markOngoing/<int:trekId>")
def markOngoing(trekId):
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    cursor.execute("Update Trek set Status='Ongoing' where trekId=?",(trekId,))
    conn.commit()
    conn.close()
    return redirect(url_for("manageTrekS",trekId=trekId))

@app.route("/markCompleted/<int:trekId>")
def markCompleted(trekId):
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    staffId=session.get("UserId")
    cursor.execute("""Select BookingId, u.UserId, FullName, t.TrekId, t.TrekName, t.StaffId,s.FullName,t.StartDate,Duration_HRS 
        FROM Trek t, Booking b, User u, User s
        where t.Trekid=b.TrekId and b.UserId=u.UserId and t.StaffId=s.UserId and t.trekId=? and t.StaffId=?""",(trekId,staffId))
    data=cursor.fetchall()
    for rec in data:
        cursor.execute("INSERT INTO History(BookingId, TrekkerId,TrekkerName, TrekId, TrekName, StaffId, StaffName,TrekStart ,Duration_HRS) values(?,?,?,?,?,?,?,?,?)", rec)
    conn.commit()
    conn.close()
    return redirect(url_for("assignedTreks"))

@app.route("/removeParticipant/<int:trekkerId>/<int:trekId>")
def removeParticipant(trekkerId,trekId):
    conn=sqlite3.connect("TrekManagement.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor=conn.cursor()
    StaffId=session.get("UserId")
    cursor.execute("DELETE from Booking where TrekId=? and UserId=?",(trekId,trekkerId))
    cursor.execute("Update Trek set Participants=Participants-1 where trekId=?",(trekId,))
    conn.commit()
    conn.close()
    return redirect(url_for("staffTrekkers"))

@app.route('/userDashboard')
def userDashboard():
    return render_template("userDashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)