from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import hashlib  # 1. Added the hashlib library

app = Flask(__name__)
app.secret_key = 'nittany_auction_secret'

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

    session['email'] = email

    cursor.execute("SELECT email FROM Helpdesk WHERE email = ?", (email,))
    if cursor.fetchone():
        session['role'] = 'helpdesk'
        conn.close()
        return redirect(url_for("helpdesk_dashboard"))

    cursor.execute("SELECT email FROM Sellers WHERE email = ?", (email,))
    if cursor.fetchone():
        session['role'] = 'seller'
        conn.close()
        return redirect(url_for("seller_dashboard"))

    cursor.execute("SELECT email FROM Local_Vendors WHERE email = ?", (email,))
    if cursor.fetchone():
        session['role'] = 'seller'
        conn.close()
        return redirect(url_for("seller_dashboard"))

    cursor.execute("SELECT email FROM Bidders WHERE email = ?", (email,))
    if cursor.fetchone():
        session['role'] = 'bidder'
        conn.close()
        return redirect(url_for("bidder_dashboard"))
    
    conn.close()
    return redirect(url_for("bidder_dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/bidder")
# refreshes the bidder dashboard with the category the user clicked on, or Root if they just logged in.
def bidder_dashboard():
    if 'email' not in session or session.get('role') != 'bidder':
        return redirect(url_for("login"))
    current_category = request.args.get("category", "Root")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT category_name FROM Categories WHERE parent_category = ?",
        (current_category,)
    )
    subcategories = [row[0] for row in cursor.fetchall()]

    products = []
    if current_category != "Root":
        cursor.execute(
            """SELECT Seller_Email, Listing_ID, Auction_Title,
                      Product_Name, Reserve_Price
               FROM Auction_Listings
               WHERE Category = ? AND Status = 1""",
            (current_category,)
        )
        products = cursor.fetchall()

    conn.close()

    return render_template(
        "bidder.html",
        current_category=current_category,
        subcategories=subcategories,
        products=products,
    )


@app.route("/profile/update", methods=["POST"])
def profile_update():
    if 'email' not in session:
        return redirect(url_for("login"))

    email = session['email']  # always from session, never from form

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    new_password = request.form.get('new_password', '').strip()
    confirm_pass = request.form.get('confirm_password', '').strip()

    cursor.execute("SELECT email FROM Bidders WHERE email = ?", (email,))
    is_bidder = cursor.fetchone()

    if is_bidder:
        cursor.execute("""
                UPDATE Bidders
                SET first_name = ?,
                    last_name  = ?,
                    age        = ?,
                    phone_number = ?,
                    major      = ?
                WHERE email = ?
            """, (
            request.form.get("first_name"),
            request.form.get("last_name"),
            request.form.get("age") or None,
            request.form.get("phone_number"),
            request.form.get("major"),
            email
        ))
        redirect_to = "bidder_dashboard"

    else:
        # Seller — only password is updatable
        redirect_to = "seller_dashboard"

    if new_password:
        if new_password != confirm_pass:
            conn.close()
            return redirect(url_for(redirect_to))
        cursor.execute(
            "UPDATE Users SET password = ? WHERE email = ?",
            (hash_password(new_password), email)
        )

    conn.commit()
    conn.close()
    return redirect(url_for(redirect_to))

@app.route("/seller")
def seller_dashboard():
    if 'email' not in session or session.get('role') != 'seller':
        return redirect(url_for("login"))
    return render_template("seller.html")


@app.route("/helpdesk")
def helpdesk_dashboard():
    if 'email' not in session or session.get('role') != 'helpdesk':
        return redirect(url_for("login"))
    return render_template("helpdesk.html")


@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/sell-product-dashboard")
def sell_product_dashboard():
    # load all categories from the database to populate the dropdown menu in the sell product dashboard
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT category_name FROM Categories ORDER BY category_name")
    categories = [{"category_name": row[0]} for row in cursor.fetchall()]
    conn.close()
    return render_template("sell-product-dashboard.html", categories=categories)


@app.route("/temporary-dashboard")
def temporary_dashboard():
    return render_template("temp-dashboard.html")

@app.route("/my-bids-dashboard")
def my_bids_dashboard():
    return render_template("my-bids-dashboard.html")

@app.route("/update-bidder-info")
def update_bidder_info():
    if 'email' not in session or session.get('role') != 'bidder':
        return redirect(url_for("login"))

    email = session['email']

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Bidders WHERE email = ?", (email,))
    bidder = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM Credit_Cards WHERE Owner_email = ? LIMIT 1",
        (email,)
    )
    card = cursor.fetchone()

    conn.close()

    if not bidder:
        return redirect(url_for("login"))

    return render_template("Update-bidder-info.html", bidder=bidder, card=card)

@app.route("/update-seller-info")
def update_seller_info():
    if 'email' not in session or session.get('role') != 'seller':
        return redirect(url_for("login"))

    email = session['email']

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Sellers WHERE email = ?", (email,))
    seller = cursor.fetchone()

    conn.close()

    if not seller:
        return redirect(url_for("login"))
    return render_template("Update-seller-info.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
