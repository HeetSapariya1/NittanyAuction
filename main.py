from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import hashlib

app = Flask(__name__)

def hash_password(password):
    return hashlib.sha256(str(password).encode('utf-8')).hexdigest()


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        email = request.form.get('email').strip()
        pw = request.form.get('password')
        hashed_pw = hash_password(pw)

        conn = sqlite3.connect('.db')
        cursor = conn.cursor()

        # Authenticate
        cursor.execute("SELECT * FROM Users WHERE email = ? AND password = ?", (email, hashed_pw))
        if not cursor.fetchone():
            conn.close()
            return "<h1>Login Failed: Invalid credentials</h1>"  # Simple error handling

        # Role Routing
        cursor.execute("SELECT email FROM Bidders WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return redirect(url_for('bidder_dashboard'))

        cursor.execute("SELECT email FROM Sellers WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return redirect(url_for('seller_dashboard'))

        cursor.execute("SELECT email FROM Helpdesk WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return redirect(url_for('helpdesk_dashboard'))

        cursor.execute("SELECT email FROM Local_Vendors WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return redirect(url_for('seller_dashboard'))

        conn.close()
        return "<h1>Logged in, but no role found.</h1>"


@app.route('/bidder')
def bidder_dashboard():
    return render_template("")


@app.route('/seller')
def seller_dashboard():
    return render_template("")


@app.route('/helpdesk')
def helpdesk_dashboard():
    return render_template("")


if __name__ == '__main__':
    app.run(debug=True)
