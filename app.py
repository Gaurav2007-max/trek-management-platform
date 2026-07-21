from flask import Flask, render_template, request, redirect, url_for
import sqlite3 

app=Flask(__name__)
conn = sqlite3.connect(
    "TrekManagement.db",
    check_same_thread=False
)
cursor=conn.cursor()

@app.route('/login',methods={"GET","POST"})
@app.route('/',methods={"GET","POST"})
def login():
    if(request.method=="POST"):
        username=request.form.get("Username")
        password=request.form.get("Password")
        cursor.execute("Select * from User where UserEmail=? AND UserPassword=?",(username,password))
        userInfo=cursor.fetchone()
        if(userInfo):
            if(userInfo[4]=="Admin"):
                return render_template("adminDashboard.html",userinfo=userInfo)
            elif(userInfo[4]=="Staff"):
                return render_template("staffDashboard.html",userinfo=userInfo)
            else:
                return render_template("userDashboard.html",userinfo=userInfo)
        else:
            return redirect("login")
        
    return render_template("login.html")

@app.route('/register',methods={"GET","POST"})
def register():
    if(request.method=="POST"):
        name=request.form.get("Fullname")
        email=request.form.get("Email")
        password=request.form.get("Password")
        password2=request.form.get("Password2")
        contact=request.form.get("Contact")
        role=request.form.get("Role")
        if(password!=password2):
            return redirect('register')
        if(role=="Trekker"):
            cursor.execute("Insert into User (UserId,FullName,UserEmail,UserPassword,UserRole,Contact) values(?,?,?,?,?,?)",(None,name,email,password,role,contact))
            conn.commit()
            return redirect('login')
        else:
            cursor.execute("Insert into StaffReq (ReqId,Name,Email,Contact,Password) values(?,?,?,?,?)",(None,name,email,contact,password))
            conn.commit()
            return redirect('/')
    return render_template("register.html")

if __name__=="__main__":
    app.run()