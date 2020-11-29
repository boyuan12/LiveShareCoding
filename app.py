from helpers import login_required, random_str
from flask import Flask, request, render_template, flash, session, redirect
from flask_socketio import SocketIO, emit
import os
from werkzeug.security import generate_password_hash, check_password_hash


if os.getenv("production") != str(True):
    import sqlite3
    conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
    c = conn.cursor()


app = Flask(__name__)
socketio = SocketIO(app)
app.config["SECRET_KEY"] = "secretkey"


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        if username == '' or password == '' or email == '':
            flash("Please fill out all required fields", category="danger")
            return render_template("register.html")

        user = c.execute("SELECT * FROM users WHERE username=:username OR email=:email", {"username": username, "email": email}).fetchall()

        if len(user) != 0:
            flash("Email or Username already exist, please change.", category="danger")
            return render_template("register.html")

        pwhash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)

        c.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)", {"username": username, "email": email, "password": pwhash})
        conn.commit()

        user = c.execute("SELECT * FROM users WHERE email=:email", {"email": email}).fetchall()
        session["user_id"] = user[0][0]

        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = c.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchall()

        if len(user) != 1:
            flash("Invalid credentials, try again.", category="danger")
            return render_template("login.html")

        if not check_password_hash(user[0][3], password):
            flash("Invalid credentials, try again.", category="danger")
            return render_template("login.html")

        session["user_id"] = user[0][0]

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/new")
@login_required
def new_live_code_session():
    invite = random_str()
    c.execute(f'INSERT INTO sessions (code, owner_id, invite) VALUES (:code, :owner_id, :invite)', {"owner_id": session.get("user_id"), "invite": invite, "code": "console.log('Hello world!')"})
    conn.commit()

    return redirect(f"/s/{invite}")


@app.route("/s/<string:invite>")
def view_session(invite):
    s = c.execute("SELECT * FROM sessions WHERE invite=:invite", {"invite": invite}).fetchall()[0]
    return render_template("editor.html", s=s, user_id=session.get("user_id"))


@socketio.on("code modified")
def code_modified(data):
    print(data["code"])
    emit("modify code", {
        "code": data["code"],
        "id": data["id"],
        "user_id": session.get("user_id")
    }, broadcast=True)

