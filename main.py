from flask import Flask, flash, render_template, request, redirect, url_for, session
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
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("login"))

@app.route("/bidder")
def bidder_dashboard():
    if 'email' not in session or session.get('role') != 'bidder':
        return redirect(url_for("login"))

    current_category = request.args.get("category", "Root")
    keyword = request.args.get("q", "").strip()
    # load all categories from the database to populate the dropdown menu
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT category_name FROM Categories WHERE parent_category = ?",
        (current_category,)
    )
    subcategories = [row[0] for row in cursor.fetchall()]

    # If keyword is entered, search across all active listings
    # Otherwise show products in the current category as before
    if keyword:
        cursor.execute("""
                    SELECT DISTINCT al.Seller_Email, al.Listing_ID, al.Auction_Title,
                           al.Product_Name, al.Reserve_Price
                    FROM Auction_Listings al
                    LEFT JOIN Bidders b ON al.Seller_Email = b.email
                    WHERE al.Status = 1
                    AND (
                        al.Auction_Title        LIKE ?
                        OR al.Product_Name      LIKE ?
                        OR al.Product_Description LIKE ?
                        OR al.Category          LIKE ?
                        OR b.first_name         LIKE ?
                        OR b.last_name          LIKE ?
                    )
                """, [f"%{keyword}%"] * 6)
    elif current_category != "Root":
        cursor.execute("""
                    SELECT Seller_Email, Listing_ID, Auction_Title,
                           Product_Name, Reserve_Price
                    FROM Auction_Listings
                    WHERE Category = ? AND Status = 1
                """, (current_category,))
    else:
        cursor.execute("SELECT 0 WHERE 0")  # empty — Root has no products

    products = cursor.fetchall()
    conn.close()

    return render_template("bidder.html", current_category=current_category, subcategories=subcategories,products=products,keyword=keyword)


@app.route("/profile/update", methods=["POST"])
def profile_update():
    if 'email' not in session:
        return redirect(url_for("login"))

    email = session['email']
    role  = session.get('role')

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    new_password = request.form.get('new_password', '').strip()
    confirm_pass = request.form.get('confirm_password', '').strip()

    if role == 'bidder':
        cursor.execute("""
                UPDATE Bidders
                SET first_name   = ?,
                    last_name    = ?,
                    age          = ?,
                    phone_number = ?,
                    major        = ?
                WHERE email = ?
            """, (
            request.form.get("first_name"),
            request.form.get("last_name"),
            request.form.get("age") or None,
            request.form.get("phone_number"),
            request.form.get("major"),
            email
        ))
        redirect_to = "update_bidder_info"

    elif role == 'seller':
        redirect_to = "update_seller_info"

    if new_password:
        if new_password != confirm_pass:
            conn.close()
            return redirect(url_for(redirect_to) + "?error=Passwords+do+not+match")
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

    # load all categories from the database to populate the dropdown menu
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT category_name FROM Categories WHERE parent_category = 'Root' ORDER BY category_name")
    categories = [{"category_name": row[0]} for row in cursor.fetchall()]
    conn.close()
    return render_template("seller.html", categories=categories)


@app.route("/helpdesk")
def helpdesk_dashboard():
    if 'email' not in session or session.get('role') != 'helpdesk':
        return redirect(url_for("login"))
    return render_template("helpdesk.html")


@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/sell-product-dashboard", methods=["GET", "POST"])
def sell_product_dashboard():
    if 'email' not in session or session.get('role') != 'seller':
        return redirect(url_for("login"))

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    if request.method == "POST":
        auction_title = request.form.get("auction_title", "").strip()
        product_name = request.form.get("product_name", "").strip()
        product_description = request.form.get("product_description", "").strip()
        reserve_price_raw = request.form.get("reserve_price", "").strip()
        max_bids_raw = request.form.get("max_bids", "").strip()
        quantity_raw = request.form.get("quantity", "").strip()
        category = request.form.get("category", "").strip()

        error = None

        if not auction_title or not product_name or not reserve_price_raw or not max_bids_raw or not category:
            error = "Please fill in all required fields."
        else:
            try:
                reserve_price = float(reserve_price_raw.replace("$", "").replace(",", ""))
                max_bids = int(max_bids_raw)
                quantity = int(quantity_raw) if quantity_raw else 1
                if reserve_price < 0 or max_bids < 1 or quantity < 1:
                    error = "Reserve price must be 0 or more, and quantity/max bids must be at least 1."
            except ValueError:
                error = "Reserve price, quantity, and max bids must be valid numbers."

        if error is None:
            cursor.execute(
                "SELECT 1 FROM Categories WHERE category_name = ?",
                (category,)
            )
            if cursor.fetchone() is None:
                error = "Please select a valid category."

        if error is None:
            cursor.execute(
                """SELECT COALESCE(MAX(Listing_ID), 0) + 1
                   FROM Auction_Listings
                   WHERE Seller_Email = ?""",
                (session['email'],)
            )
            next_listing_id = cursor.fetchone()[0]

            cursor.execute(
                """INSERT INTO Auction_Listings (
                       Seller_Email, Listing_ID, Category, Auction_Title,
                       Product_Name, Product_Description, Quantity,
                       Reserve_Price, Max_Bids, Status
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (
                    session['email'],
                    next_listing_id,
                    category,
                    auction_title,
                    product_name,
                    product_description or None,
                    quantity,
                    reserve_price,
                    max_bids,
                )
            )
            conn.commit()

            cursor.execute("SELECT category_name FROM Categories WHERE parent_category = 'Root' ORDER BY category_name")
            categories = [{"category_name": row[0]} for row in cursor.fetchall()]
            conn.close()
            return render_template(
                "sell-product-dashboard.html",
                categories=categories,
                success="Product listed successfully."
            )

        cursor.execute("SELECT category_name FROM Categories WHERE parent_category = 'Root' ORDER BY category_name")
        categories = [{"category_name": row[0]} for row in cursor.fetchall()]
        conn.close()
        return render_template(
            "sell-product-dashboard.html",
            categories=categories,
            error=error
        )

    # load all categories from the database to populate the dropdown menu in the sell product dashboard
    cursor.execute("SELECT category_name FROM Categories WHERE parent_category = 'Root' ORDER BY category_name")
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

        return render_template("Update-seller-info.html", seller=seller)

if __name__ == "__main__":
    app.run(debug=True)
