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

    cursor.execute("SELECT email FROM Sellers WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return redirect(url_for("seller_dashboard"))

    cursor.execute("SELECT email FROM Local_Vendors WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return redirect(url_for("seller_dashboard"))

    cursor.execute("SELECT email FROM Bidders WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return redirect(url_for("bidder_dashboard"))
    
    conn.close()
    return redirect(url_for("bidder_dashboard"))


@app.route("/bidder")
# refreshes the bidder dashboard with the category the user clicked on, or Root if they just logged in.
def bidder_dashboard():
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


@app.route("/profile/update", methods=["Get", "POST"])
def profile_update():
    email = request.form.get('email', '').strip()

    if not email:
        return redirect(url_for("login"))

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    new_password = request.form.get('new_password', '').strip()
    confirm_pass = request.form.get('confirm_password', '').strip()

    # Check role by querying the DB
    cursor.execute("SELECT email FROM Bidders WHERE email = ?", (email,))
    if cursor.fetchone():
        cursor.execute('''
            UPDATE Bidders
            SET first_name = ?, last_name = ?, age = ?, phone_number = ?, major = ?
            WHERE email = ?
        ''', (
            request.form.get('first_name', '').strip(),
            request.form.get('last_name', '').strip(),
            request.form.get('age', '').strip() or None,
            request.form.get('phone_number', '').strip(),
            request.form.get('major', '').strip(),
            email
        ))
        redirect_to = "bidder_dashboard"
    else:
        # Must be a seller — only password is updatable
        redirect_to = "seller_dashboard"

    if new_password:
        if new_password != confirm_pass:
            conn.close()
            return redirect(url_for(redirect_to, error="Passwords do not match"))
        cursor.execute(
            "UPDATE Users SET password = ? WHERE email = ?",
            (hash_password(new_password), email)
        )

    conn.commit()
    conn.close()
    return redirect(url_for(redirect_to))

@app.route("/seller")
def seller_dashboard():
    return render_template("seller.html")


@app.route("/helpdesk")
def helpdesk_dashboard():
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
    return render_template("Update-bidder-info.html")

@app.route("/update-bidder-info")
def update_seller_info():
    return render_template("Update-seller-info.html")
if __name__ == "__main__":
    app.run(debug=True)
