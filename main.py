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

    selected_category = request.args.get("category", "").strip()
    search_query = request.args.get("q", "").strip()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Every category, flat, for the dropdown
    cursor.execute("SELECT category_name FROM Categories WHERE parent_category = 'Root' ORDER BY category_name")
    categories = [{"category_name": row[0]} for row in cursor.fetchall()]

    # Build the listings query dynamically so we can combine category + search
    sql = """SELECT Seller_Email, Listing_ID, Auction_Title, Product_Name, Reserve_Price
             FROM Auction_Listings
             WHERE Status = 1"""
    params = []
    if selected_category:
        sql += " AND Category = ?"
        params.append(selected_category)
    if search_query:
        sql += """ AND (Auction_Title    LIKE ?
                    OR Product_Name      LIKE ?
                    OR Product_Description LIKE ?
                    OR Category          LIKE ?
                    OR Seller_Email      LIKE ?)"""
        like = f"%{search_query}%"
        params.extend([like, like, like, like, like])
    sql += " ORDER BY Auction_Title LIMIT 60"

    cursor.execute(sql, params)
    products = cursor.fetchall()
    conn.close()

    return render_template(
        "bidder.html",
        categories=categories,
        products=products,
        selected_category=selected_category,
        search_query=search_query,
    )



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

    premium_only = request.args.get("premium") == "1"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT category_name FROM Categories WHERE parent_category = 'Root' ORDER BY category_name")
    categories = [{"category_name": row[0]} for row in cursor.fetchall()]

    sql = """SELECT Listing_ID, Category, Auction_Title, Product_Name,
                    Product_Description, Premium_Item, Quantity, Reserve_Price, Max_Bids, Status
             FROM Auction_Listings
             WHERE Seller_Email = ?"""
    params = [session['email']]

    if premium_only:
        sql += " AND Premium_Item = 1"

    sql += " ORDER BY Listing_ID DESC"

    cursor.execute(sql, params)
    seller_listings = cursor.fetchall()

    conn.close()
    return render_template(
        "seller.html",
        categories=categories,
        seller_listings=seller_listings,
        seller_email=session['email'],
        premium_only=premium_only,
    )


@app.route("/helpdesk")
def helpdesk_dashboard():
    if 'email' not in session or session.get('role') != 'helpdesk':
        return redirect(url_for("login"))
    return render_template("helpdesk.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    form = request.form
    email = form.get("email", "").strip()
    role = form.get("role", "Bidder")

    if role == "HelpDesk":
        flash("External registration for HelpDesk is not permitted.", "error")
        return redirect(url_for("register"))

    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("INSERT INTO Users (email, password) VALUES (?, ?)",
                           (email, hash_password(form.get("password", ""))))

            if role in ["Bidder", "Seller"]:
                cursor.execute("""
                               INSERT INTO Bidders (email, first_name, last_name, age, major, home_address_id)
                               VALUES (?, ?, ?, ?, ?, ?)
                               """, (
                                   email,
                                   form.get("first_name"),
                                   form.get("last_name"),
                                   form.get("age") or None,
                                   form.get("major"),
                                   form.get("home_address_id") or None
                               ))

            if role in ["Seller", "LocalVendor"]:
                cursor.execute("""
                               INSERT INTO Sellers (email, bank_routing_number, bank_account_number, balance)
                               VALUES (?, ?, ?, 0.0)
                               """, (email, form.get("bank_routing_number"), form.get("bank_account_number")))

            if role == "LocalVendor":
                cursor.execute("""
                               INSERT INTO Local_Vendors (email, business_name, business_address_id,
                                                          customer_service_phone_number)
                               VALUES (?, ?, ?, ?)
                               """, (
                                   email,
                                   form.get("business_name"),
                                   form.get("business_address_id") or None,
                                   form.get("customer_service_phone_number")
                               ))

    except sqlite3.IntegrityError:
        # validity check
        flash("Registration failed. Email already exists or Address ID is invalid.", "error")
        return redirect(url_for("register"))

    # Log them in
    session['email'] = email
    session['role'] = "Seller" if role in ["Seller", "LocalVendor"] else "Bidder"

    flash("Registration successful! Welcome to Nittany Auction.", "success")

    # redirect based on correct role
    if session['role'] == "Bidder":
        return redirect(url_for("bidder_dashboard"))
    else:
        return redirect(url_for("seller_dashboard"))

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
        premium_item = 1 if request.form.get("premium_item") == "1" else 0

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
                       Product_Name, Product_Description, Premium_Item, Quantity,
                       Reserve_Price, Max_Bids, Status
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (
                    session['email'],
                    next_listing_id,
                    category,
                    auction_title,
                    product_name,
                    product_description or None,
                    premium_item,
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

@app.route("/place-bid", methods=["POST"])
def place_bid():
    if 'email' not in session or session.get('role') != 'bidder':
        return redirect(url_for("login"))

    seller_email = request.form.get("seller_email", "").strip()
    listing_id   = request.form.get("listing_id", "").strip()
    try:
        bid_price = float(request.form.get("bid_price", "").strip())
    except ValueError:
        return redirect(url_for("bidder_dashboard"))

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Bids (Seller_Email, Listing_ID, Bidder_Email, Bid_Price) "
        "VALUES (?, ?, ?, ?)",
        (seller_email, listing_id, session['email'], bid_price)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("my_bids_dashboard"))

@app.route("/my-bids-dashboard")
def my_bids_dashboard():
    if 'email' not in session or session.get('role') != 'bidder':
        return redirect(url_for("login"))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT AL.Auction_Title, B.Seller_Email, B.Bid_Price
             FROM Bids B
             JOIN Auction_Listings AL
               ON AL.Seller_Email = B.Seller_Email
              AND AL.Listing_ID   = B.Listing_ID
            WHERE B.Bidder_Email = ?
            ORDER BY B.Bid_ID DESC""",
        (session['email'],)
    )
    my_bids = cursor.fetchall()
    conn.close()
    return render_template("my-bids-dashboard.html", my_bids=my_bids)

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
