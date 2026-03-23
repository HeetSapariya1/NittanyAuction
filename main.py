from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import hashlib  # 1. Added the hashlib library

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database_population/nittany_auction.db")

def hash_password(plain: str) -> str:
    return hashlib.sha256(str(plain).encode()).hexdigest()


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    raw_password = request.form.get("password", "")

    hashed_password = hash_password(raw_password)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Pass the newly hashed_password into the query instead of the raw text
    cursor.execute(
        "SELECT * FROM Users WHERE email = ? AND password = ?",
        (email, hashed_password)
    )
    user = cursor.fetchone()

    if user is None:
        conn.close()
        return render_template("login.html", error="Invalid email or password")

    cursor.execute("SELECT email FROM Helpdesk WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return redirect(url_for("helpdesk_dashboard"))

    cursor.execute("SELECT email FROM Bidders WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return redirect(url_for("bidder_dashboard"))

    cursor.execute("SELECT email FROM Sellers WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return redirect(url_for("seller_dashboard"))

    cursor.execute("SELECT email FROM Local_Vendors WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return redirect(url_for("seller_dashboard"))

    conn.close()
    return redirect(url_for("temporary_dashboard"))


@app.route("/bidder")
def bidder_dashboard():
    return render_template("bidder.html")


@app.route("/seller")
def seller_dashboard():
    return render_template("seller.html")


@app.route("/helpdesk")
def helpdesk_dashboard():
    return render_template("helpdesk.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/temporary-dashboard")
def temporary_dashboard():
    return render_template("temp-dashboard.html")




if __name__ == "__main__":
    app.run(debug=True)
