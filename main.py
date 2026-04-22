from flask import Flask, flash, render_template, request, redirect, url_for, session
import sqlite3
import os
import hashlib  # 1. Added the hashlib library
from datetime import datetime, timezone

app = Flask(__name__)
app.secret_key = 'nittany_auction_secret'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database_population/nittany_auction.db")

def hash_password(plain: str) -> str:
    return hashlib.sha256(str(plain).encode()).hexdigest()


def user_has_bidder_access(email):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM Bidders WHERE email = ?", (email,))
    has_bidder = cursor.fetchone() is not None
    conn.close()
    return has_bidder


def user_has_seller_access(email):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM Sellers WHERE email = ?", (email,))
    has_seller = cursor.fetchone() is not None
    conn.close()
    return has_seller


def build_seller_dashboard_redirect_args(premium="", status_filter="all", category_filter=""):
    redirect_args = {}
    if premium == "1":
        redirect_args["premium"] = "1"
    if status_filter and status_filter != "all":
        redirect_args["status"] = status_filter
    if category_filter:
        redirect_args["category"] = category_filter
    return redirect_args


def validate_listing_form(form):
    auction_title = form.get("auction_title", "").strip()
    product_name = form.get("product_name", "").strip()
    product_description = form.get("product_description", "").strip()
    reserve_price_raw = form.get("reserve_price", "").strip()
    max_bids_raw = form.get("max_bids", "").strip()
    quantity_raw = form.get("quantity", "").strip()
    category = form.get("category", "").strip()
    premium_item = 1 if form.get("premium_item") else 0

    if not auction_title or not product_name or not reserve_price_raw or not max_bids_raw or not category:
        return None, "Please fill in all required fields."

    try:
        reserve_price = float(reserve_price_raw.replace("$", "").replace(",", ""))
        max_bids = int(max_bids_raw)
        quantity = int(quantity_raw) if quantity_raw else 1
    except ValueError:
        return None, "Reserve price, quantity, and max bids must be valid numbers."

    if reserve_price < 0 or max_bids < 1 or quantity < 1:
        return None, "Reserve price must be 0 or more, and quantity/max bids must be at least 1."

    listing_values = {
        "auction_title": auction_title,
        "product_name": product_name,
        "product_description": product_description or None,
        "reserve_price": reserve_price,
        "max_bids": max_bids,
        "quantity": quantity,
        "category": category,
        "premium_item": premium_item,
    }
    return listing_values, None


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


@app.route("/switch-dashboard/<target>")
def switch_dashboard(target):
    if 'email' not in session:
        return redirect(url_for("login"))

    email = session['email']
    target = target.strip().lower()

    if target == "bidder" and user_has_bidder_access(email):
        session['role'] = 'bidder'
        return redirect(url_for("bidder_dashboard"))

    if target == "seller" and user_has_seller_access(email):
        session['role'] = 'seller'
        return redirect(url_for("seller_dashboard"))

    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("login"))

@app.route("/bidder")
def bidder_dashboard():
    '''
    Bidder Dashboard - Displays the active listings to all bidder users 
    Filters out premium listings such that only premium members can view them
    Categories separate dynamically through a drop-down 
    '''
    if 'email' not in session or session.get('role') != 'bidder':
        return redirect(url_for("login"))

    selected_category = request.args.get("category", "").strip()
    search_query = request.args.get("q", "").strip()
    premium_only = request.args.get("premium") == "1"

    email = session['email']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT Premium_User FROM Bidders WHERE email = ?", (email,))
    row = cursor.fetchone()
    is_premium = row[0] == 1 if row else False

    if not is_premium:
        premium_only = False

    # Every category, flat, for the dropdown
    cursor.execute("SELECT category_name FROM Categories WHERE parent_category = 'Root' ORDER BY category_name")
    categories = [{"category_name": row[0]} for row in cursor.fetchall()]

    # Build the listings query dynamically so we can combine category + search
    # When status = 1 only active lostings are listed 
    sql = """SELECT Seller_Email, Listing_ID, Auction_Title, Product_Name, Reserve_Price
             FROM Auction_Listings
             WHERE Status = 1 AND Seller_Email != ?"""
    params = [email]
    if not is_premium:
        sql += " AND (Premium_Item = 0 OR Premium_Item IS NULL)"
    if selected_category:
        sql += " AND Category = ?"
        params.append(selected_category)
    if premium_only:
        sql += " AND Premium_Item = 1"
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
        premium_only=premium_only,
        is_premium=is_premium,
        can_switch_to_seller=user_has_seller_access(email)
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
        premium = 1 if request.form.get('premium_user') else 0
        cursor.execute("""
                UPDATE Bidders
                SET first_name   = ?,
                    last_name    = ?,
                    age          = ?,
                    phone_number = ?,
                    major        = ?,
                    Premium_User = ?
                WHERE email = ?
            """, (
            request.form.get("first_name"),
            request.form.get("last_name"),
            request.form.get("age") or None,
            request.form.get("phone_number"),
            request.form.get("major"),
            premium,
            email
        ))
        redirect_to = "update_bidder_info"

    elif role == 'seller':
        cursor.execute("""
                UPDATE Sellers
                SET bank_routing_number = ?,
                    bank_account_number = ?
                WHERE email = ?
            """, (
            request.form.get("bank_routing_number"),
            request.form.get("bank_account_number"),
            email
        ))
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
    status_filter = request.args.get("status", "all").strip().lower()
    selected_category = request.args.get("category", "").strip()
    status_map = {"inactive": 0, "active": 1, "sold": 2}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT category_name FROM Categories WHERE parent_category = 'Root' ORDER BY category_name")
    categories = [{"category_name": row[0]} for row in cursor.fetchall()]


    sql = """SELECT AL.Listing_ID, AL.Category, AL.Auction_Title, AL.Product_Name,
                    AL.Product_Description, AL.Premium_Item, AL.Quantity, AL.Reserve_Price, AL.Max_Bids,
                    AL.Remaining_Bids, AL.Status, AL.Removal_Reason,
                    (SELECT COUNT(*) FROM Bids B
                     WHERE B.Seller_Email = AL.Seller_Email AND B.Listing_ID = AL.Listing_ID) AS Bid_Count
             FROM Auction_Listings
             AL
             WHERE AL.Seller_Email = ?"""
    params = [session['email']]

    if premium_only:
        sql += " AND Premium_Item = 1"

    if selected_category:
        sql += " AND Category = ?"
        params.append(selected_category)

    if status_filter in status_map:
        sql += " AND Status = ?"
        params.append(status_map[status_filter])
    else:
        status_filter = "all"

    sql += " ORDER BY Listing_ID DESC"

    cursor.execute(sql, params)
    seller_listings = cursor.fetchall()

    cursor.execute("""
        SELECT AVG(Rating)
        FROM Ratings
        WHERE Seller_Email = ?
    """, (session['email'],))

    avg_rating = cursor.fetchone()[0]
    conn.close()
    return render_template(
        "seller.html",
        categories=categories,
        seller_listings=seller_listings,
        seller_email=session['email'],
        premium_only=premium_only,
        status_filter=status_filter,
        selected_category=selected_category,
        update_error=request.args.get("update_error", "").strip(),
        update_success=request.args.get("update_success", "").strip(),
        edit_listing_id=request.args.get("edit_listing_id", "").strip(),
        avg_rating=avg_rating,
        can_switch_to_bidder=user_has_bidder_access(session['email'])
    )


@app.route("/seller/listing-status", methods=["POST"])
def update_listing_status():
    if 'email' not in session or session.get('role') != 'seller':
        return redirect(url_for("login"))

    listing_id = request.form.get("listing_id", "").strip()
    new_status = request.form.get("status", "").strip()
    premium = request.form.get("premium", "").strip()
    status_filter = request.form.get("status_filter", "all").strip().lower()
    category_filter = request.form.get("category_filter", "").strip()
    removal_reason = request.form.get("removal_reason", "").strip()

    status_map = {"0", "1"}
    if not listing_id.isdigit() or new_status not in status_map:
        return redirect(url_for("seller_dashboard", premium=premium, status=status_filter, category=category_filter))

    removal_reason_value = (removal_reason or None) if int(new_status) == 0 else None

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.execute(
        """SELECT Status,
                  (SELECT COUNT(*) FROM Bids B
                   WHERE B.Seller_Email = Auction_Listings.Seller_Email
                     AND B.Listing_ID = Auction_Listings.Listing_ID) AS Bid_Count
           FROM Auction_Listings
           WHERE Seller_Email = ? AND Listing_ID = ?""",
        (session['email'], int(listing_id))
    )
    listing = cursor.fetchone()

    redirect_args = build_seller_dashboard_redirect_args(premium, status_filter, category_filter)

    if listing is None:
        conn.close()
        redirect_args["update_error"] = "Listing not found."
        return redirect(url_for("seller_dashboard", **redirect_args))

    current_status, bid_count = listing

    if int(new_status) == 0 and bid_count > 0:
        conn.close()
        redirect_args["update_error"] = "This listing cannot be set to inactive because bidding has already started."
        return redirect(url_for("seller_dashboard", **redirect_args))

    if current_status == 2:
        conn.close()
        redirect_args["update_error"] = "Sold listings cannot be changed here."
        return redirect(url_for("seller_dashboard", **redirect_args))

    cursor.execute(
        """UPDATE Auction_Listings
           SET Status = ?,
               Removal_Reason = ?
           WHERE Seller_Email = ? AND Listing_ID = ?""",
        (
            int(new_status),
            removal_reason_value,
            session['email'],
            int(listing_id),
        )
    )
    conn.commit()
    conn.close()

    return redirect(url_for("seller_dashboard", **redirect_args))


@app.route("/seller/update-listing", methods=["POST"])
def update_listing():
    if 'email' not in session or session.get('role') != 'seller':
        return redirect(url_for("login"))

    listing_id = request.form.get("listing_id", "").strip()
    premium = request.form.get("premium", "").strip()
    status_filter = request.form.get("status_filter", "all").strip().lower()
    category_filter = request.form.get("category_filter", "").strip()

    redirect_args = build_seller_dashboard_redirect_args(premium, status_filter, category_filter)
    redirect_args["edit_listing_id"] = listing_id

    if not listing_id.isdigit():
        redirect_args["update_error"] = "Invalid listing selected."
        return redirect(url_for("seller_dashboard", **redirect_args))

    listing_values, error = validate_listing_form(request.form)
    if error:
        redirect_args["update_error"] = error
        return redirect(url_for("seller_dashboard", **redirect_args))

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM Categories WHERE category_name = ?",
        (listing_values["category"],)
    )
    if cursor.fetchone() is None:
        conn.close()
        redirect_args["update_error"] = "Please select a valid category."
        return redirect(url_for("seller_dashboard", **redirect_args))

    cursor.execute(
        """SELECT Status, Max_Bids, Remaining_Bids,
                  (SELECT COUNT(*) FROM Bids B
                   WHERE B.Seller_Email = Auction_Listings.Seller_Email
                     AND B.Listing_ID = Auction_Listings.Listing_ID) AS Bid_Count
           FROM Auction_Listings
           WHERE Seller_Email = ? AND Listing_ID = ?""",
        (session['email'], int(listing_id))
    )
    listing = cursor.fetchone()

    if listing is None:
        conn.close()
        redirect_args["update_error"] = "Listing not found."
        return redirect(url_for("seller_dashboard", **redirect_args))

    current_status, current_max_bids, current_remaining_bids, bid_count = listing

    if current_status == 2:
        conn.close()
        redirect_args["update_error"] = "Sold listings cannot be updated."
        return redirect(url_for("seller_dashboard", **redirect_args))

    if current_status == 1 and bid_count > 0:
        conn.close()
        redirect_args["update_error"] = "This active listing cannot be updated because bidding has already started."
        return redirect(url_for("seller_dashboard", **redirect_args))

    new_remaining_bids = listing_values["max_bids"]
    if current_max_bids is not None and current_remaining_bids is not None:
        bids_used = max(current_max_bids - current_remaining_bids, 0)
        if listing_values["max_bids"] < bids_used:
            conn.close()
            redirect_args["update_error"] = f"Max bids cannot be set below {bids_used} because that many bids have already been used."
            return redirect(url_for("seller_dashboard", **redirect_args))
        new_remaining_bids = max(listing_values["max_bids"] - bids_used, 0)

    cursor.execute(
        """UPDATE Auction_Listings
           SET Category = ?,
               Auction_Title = ?,
               Product_Name = ?,
               Product_Description = ?,
               Premium_Item = ?,
               Quantity = ?,
               Reserve_Price = ?,
               Max_Bids = ?,
               Remaining_Bids = ?
           WHERE Seller_Email = ? AND Listing_ID = ?""",
        (
            listing_values["category"],
            listing_values["auction_title"],
            listing_values["product_name"],
            listing_values["product_description"],
            listing_values["premium_item"],
            listing_values["quantity"],
            listing_values["reserve_price"],
            listing_values["max_bids"],
            new_remaining_bids,
            session['email'],
            int(listing_id),
        )
    )
    conn.commit()
    conn.close()

    redirect_args.pop("edit_listing_id", None)
    redirect_args["update_success"] = "Listing updated successfully."
    return redirect(url_for("seller_dashboard", **redirect_args))


@app.route("/seller/delete-listing", methods=["POST"])
def delete_listing():
    if 'email' not in session or session.get('role') != 'seller':
        return redirect(url_for("login"))

    listing_id = request.form.get("listing_id", "").strip()
    premium = request.form.get("premium", "").strip()
    status_filter = request.form.get("status_filter", "all").strip().lower()
    category_filter = request.form.get("category_filter", "").strip()
    removal_reason = request.form.get("removal_reason", "").strip()

    if not listing_id.isdigit():
        return redirect(url_for("seller_dashboard"))

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.execute(
        """SELECT Auction_Title, Status,
                  (SELECT COUNT(*) FROM Bids B
                   WHERE B.Seller_Email = Auction_Listings.Seller_Email
                     AND B.Listing_ID = Auction_Listings.Listing_ID) AS Bid_Count
           FROM Auction_Listings
           WHERE Seller_Email = ? AND Listing_ID = ?""",
        (session['email'], int(listing_id))
    )
    listing = cursor.fetchone()

    redirect_args = build_seller_dashboard_redirect_args(premium, status_filter, category_filter)

    if listing is not None and listing[2] > 0:
        conn.close()
        redirect_args["update_error"] = "This listing cannot be deleted because bidding has already started."
        return redirect(url_for("seller_dashboard", **redirect_args))

    if listing is not None:
        cursor.execute(
            """INSERT INTO Listing_Removals (
                   Seller_Email, Listing_ID, Auction_Title, Removed_Status,
                   Removal_Reason, Removed_At
               ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                session['email'],
                int(listing_id),
                listing[0],
                listing[1],
                removal_reason or None,
                datetime.now(timezone.utc).isoformat(),
            )
        )
        cursor.execute(
            """DELETE FROM Auction_Listings
               WHERE Seller_Email = ? AND Listing_ID = ?""",
            (session['email'], int(listing_id))
        )
        conn.commit()

    conn.close()

    return redirect(url_for("seller_dashboard", **redirect_args))


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

    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            cursor.execute("INSERT INTO Users (email, password) VALUES (?, ?)",
                           (email, hash_password(form.get("password", ""))))

            if role in ["Bidder", "Seller"]: # All information pertaining to both Bidder and Seller
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

            if role in ["Seller", "LocalVendor"]: # All information pertaining to both Local Vendor and Seller
                cursor.execute("""
                               INSERT INTO Sellers (email, bank_routing_number, bank_account_number, balance)
                               VALUES (?, ?, ?, 0.0)
                               """, (email, form.get("bank_routing_number"), form.get("bank_account_number")))

            if role == "LocalVendor": # All information pertaining to Local Vendor
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

    except sqlite3.IntegrityError: #Validity check 
        # validity check
        flash("Registration failed. Email already exists or Address ID is invalid.", "error")
        return redirect(url_for("register"))

    # Log them in
    session['email'] = email
    session['role'] = "seller" if role in ["Seller", "LocalVendor"] else "bidder"

    flash("Registration successful! Welcome to Nittany Auction.", "success")

    # redirect based on correct role
    if session['role'] == "bidder":
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
        listing_values, error = validate_listing_form(request.form)

        if error is None:
            cursor.execute(
                "SELECT 1 FROM Categories WHERE category_name = ?",
                (listing_values["category"],)
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
            premium_item = 1 if request.form.get("premium_item") else 0
            cursor.execute(
                """INSERT INTO Auction_Listings (
                       Seller_Email, Listing_ID, Category, Auction_Title,
                       Product_Name, Product_Description, Premium_Item, Quantity,
                       Reserve_Price, Max_Bids, Remaining_Bids, Status, Removal_Reason
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                (
                    session['email'],
                    next_listing_id,
                    listing_values["category"],
                    listing_values["auction_title"],
                    listing_values["product_name"],
                    listing_values["product_description"],
                    listing_values["premium_item"],
                    listing_values["quantity"],
                    listing_values["reserve_price"],
                    listing_values["max_bids"],
                    listing_values["max_bids"],
                    None,
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

@app.route("/auction-result/<seller_email>/<int:listing_id>")
def auction_result(seller_email, listing_id):
    '''
    Auction Result - after max_bids is reached, determine winner by taking highest bid and reserve price 
    If highest bid >= reserve price: auction is successful. 
    If highest bid < reserve price: auction unsuccessful
    '''
    if 'email' not in session or session.get('role') != 'bidder':
        return redirect(url_for("login"))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # fetch listings 
    cursor.execute("""
        SELECT Auction_Title, Reserve_Price FROM Auction_Listings
        WHERE Seller_Email = ? AND Listing_ID = ?
    """, (seller_email, listing_id))
    listing = cursor.fetchone()

    # find the highest bid
    cursor.execute("""
        SELECT Bidder_Email, Bid_Price FROM Bids
        WHERE Seller_Email = ? AND Listing_ID = ?
        ORDER BY Bid_Price DESC LIMIT 1
    """, (seller_email, listing_id))
    top = cursor.fetchone()
    conn.close()

    if not listing or not top:
        return redirect(url_for("bidder_dashboard"))

    # collect winner info 
    winner_email = top[0]
    winning_bid = top[1]
    reserve_met = winning_bid >= listing[1] # check if it meets reserve price 
    is_winner = (winner_email == session['email']) and reserve_met # check if true  

    return render_template("auction-result.html",
        title=listing[0],
        winning_bid=winning_bid,
        reserve_met=reserve_met,
        is_winner=is_winner,
        seller_email=seller_email,
        listing_id=listing_id
    )

@app.route("/auction/<seller_email>/<int:listing_id>")
def auction_detail(seller_email, listing_id):
    # View active listings from the bidder view 
    # Displays highest bid and remaining bids 
    if 'email' not in session or session.get('role') != 'bidder':
        return redirect(url_for("login"))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # retrieve listings 
    cursor.execute("""
        SELECT Seller_Email, Listing_ID, Auction_Title, Product_Name,
               Product_Description, Reserve_Price, Max_Bids, Remaining_Bids, Status, Category
        FROM Auction_Listings
        WHERE Seller_Email = ? AND Listing_ID = ?
    """, (seller_email, listing_id))
    listing = cursor.fetchone()

    # Current highest bid which is shown on page and used to compute minimum next bid
    cursor.execute("""
        SELECT MAX(Bid_Price) FROM Bids
        WHERE Seller_Email = ? AND Listing_ID = ?
    """, (seller_email, listing_id))
    row = cursor.fetchone()
    highest_bid = row[0] if row[0] is not None else 0.0

    # Turn-taking rule: fetch the most recent bidder so the template can block the form if it matches the current session user
    cursor.execute("""
        SELECT Bidder_Email FROM Bids
        WHERE Seller_Email = ? AND Listing_ID = ?
        ORDER BY Bid_ID DESC LIMIT 1 
    """, (seller_email, listing_id))
    last_row = cursor.fetchone()
    last_bidder = last_row[0] if last_row else None

    # Fetch seller's average rating and total number of ratings
    cursor.execute("""
        SELECT ROUND(AVG(Rating), 1), COUNT(*)
        FROM Ratings
        WHERE Seller_email = ?
    """, (seller_email,))
    rating_row = cursor.fetchone()
    avg_rating = rating_row[0]   # None if no ratings yet
    rating_count = rating_row[1]

    conn.close()

    if listing is None:
        return redirect(url_for("bidder_dashboard"))

    # feedback for if bids are succesful, too low, etc 
    feedback = request.args.get("feedback")
    feedback_type = request.args.get("type", "error")

    return render_template("auction-detail.html",
        listing=listing,
        highest_bid=highest_bid,
        last_bidder=last_bidder,
        feedback=feedback,
        feedback_type=feedback_type,
        current_user=session['email'],
        avg_rating=avg_rating,
        rating_count=rating_count
    )

@app.route("/payment/<seller_email>/<int:listing_id>", methods=["GET", "POST"])
def payment(seller_email, listing_id):
    '''
    After a bidder wins, take the user to a payment page 
    Check if they have payment saved, or allow them to fill in details 
    '''
    if 'email' not in session or session.get('role') != 'bidder':
        return redirect(url_for("login"))

    bidder_email = session['email']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Auction_Title, Reserve_Price FROM Auction_Listings
        WHERE Seller_Email = ? AND Listing_ID = ?
    """, (seller_email, listing_id))
    listing = cursor.fetchone()

    # find winning bid value 
    cursor.execute("""
        SELECT MAX(Bid_Price) FROM Bids
        WHERE Seller_Email = ? AND Listing_ID = ? AND Bidder_Email = ?
    """, (seller_email, listing_id, bidder_email))
    row = cursor.fetchone()
    winning_bid = row[0] if row[0] else 0.0 

    # find credit card of winner bidder 
    cursor.execute("""
        SELECT credit_card_num, card_type, expire_month, expire_year
        FROM Credit_Cards WHERE Owner_email = ? LIMIT 1
    """, (bidder_email,))
    saved_card = cursor.fetchone()

    if request.method == "POST":
        card_num      = request.form.get("credit_card_num", "").strip()
        card_type     = request.form.get("card_type", "").strip()
        expire_month  = request.form.get("expire_month", "").strip()
        expire_year   = request.form.get("expire_year", "").strip()
        security_code = request.form.get("security_code", "").strip()

        # insert card
        cursor.execute("SELECT 1 FROM Credit_Cards WHERE credit_card_num = ?", (card_num,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE Credit_Cards
                SET card_type=?, expire_month=?, expire_year=?, security_code=?, Owner_email=?
                WHERE credit_card_num=?
            """, (card_type, expire_month, expire_year, security_code, bidder_email, card_num))
        else:
            cursor.execute("""
                INSERT INTO Credit_Cards
                    (credit_card_num, card_type, expire_month, expire_year, security_code, Owner_email)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (card_num, card_type, expire_month, expire_year, security_code, bidder_email))

        # Record transaction 
        cursor.execute("""
            INSERT INTO Transactions (Seller_Email, Listing_ID, Buyer_Email, Date, Payment)
            VALUES (?, ?, ?, ?, ?)
        """, (seller_email, listing_id, bidder_email,
              datetime.now(timezone.utc).isoformat(), winning_bid))

        # update the balance 
        cursor.execute("""
            UPDATE Sellers SET balance = balance + ? WHERE email = ?
        """, (winning_bid, seller_email))

        conn.commit()
        conn.close()
        return redirect(url_for("confirmation_page", seller_email=seller_email, listing_id = listing_id))

    conn.close()
    return render_template("payment.html",
        listing=listing,
        winning_bid=winning_bid,
        saved_card=saved_card,
        seller_email=seller_email,
        listing_id=listing_id
    )

@app.route("/confirmation")
def confirmation_page():
    # redirect to confirmation page after payment received 
    if 'email' not in session or session.get('role') != 'bidder':
        return redirect(url_for("login"))
    seller_email = request.args.get("seller_email", "")
    listing_id = request.args.get("listing_id", "").strip()
    rating_feedback = request.args.get("rating_feedback", "").strip()
    rating_feedback_type = request.args.get("rating_feedback_type", "success").strip()
    return render_template(
        "confirmation-page.html",
        seller_email=seller_email,
        listing_id=listing_id,
        rating_feedback=rating_feedback,
        rating_feedback_type=rating_feedback_type
    )


@app.route("/place-bid", methods=["POST"])
def place_bid():
    '''
    Place Bids - enforces increment, auction end, and turn taking rules. 
    Redirects to payment page when a listing is sold
    '''
    if 'email' not in session or session.get('role') != 'bidder':
        return redirect(url_for("login"))

    seller_email = request.form.get("seller_email", "").strip()
    listing_id   = request.form.get("listing_id", "").strip()
    bidder_email = session['email']

    try:
        bid_price = float(request.form.get("bid_price", "").strip())
    except ValueError:
        return redirect(url_for("bidder_dashboard"))

    # Helper to reject a bid if its invalid 
    def reject(msg):
        return redirect(url_for("auction_detail",
            seller_email=seller_email, listing_id=listing_id,
            feedback=msg, type="error"))

    if seller_email == bidder_email:
        return reject("You cannot bid on your own listing.")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Fetch listing
    cursor.execute("""
        SELECT Status, Remaining_Bids, Reserve_Price, Auction_Title
        FROM Auction_Listings
        WHERE Seller_Email = ? AND Listing_ID = ?
    """, (seller_email, listing_id))
    listing = cursor.fetchone()

    # Auction end: the listing must be active and have remaining bids 
    if listing is None or listing[0] != 1 or listing[1] <= 0:
        conn.close()
        return reject("This auction is not active.")

    # Current highest bid
    cursor.execute("""
        SELECT MAX(Bid_Price) FROM Bids
        WHERE Seller_Email = ? AND Listing_ID = ?
    """, (seller_email, listing_id))
    row = cursor.fetchone()
    highest_bid = row[0] if row[0] is not None else 0.0

    # Rule 1: must be at least $1 higher
    if bid_price < highest_bid + 1.0:
        conn.close()
        return reject(f"Bid too low. Minimum bid is ${highest_bid + 1.0:.2f}.")

    if bid_price > highest_bid + 2000.0:
        conn.close()
        return reject(f"Bid too high. Maximum bid is ${highest_bid + 2000.0:.2f}.")

    # Rule 3: no consecutive bids so no bidder can match the last bidder for a given listing 
    cursor.execute("""
        SELECT Bidder_Email FROM Bids
        WHERE Seller_Email = ? AND Listing_ID = ?
        ORDER BY Bid_ID DESC LIMIT 1
    """, (seller_email, listing_id))
    last = cursor.fetchone() # find the last bidder to compare 
    if last and last[0] == bidder_email:
        conn.close()
        return reject("You placed the last bid. Wait for another bidder first.")

    # All rules passed so insert bid
    cursor.execute(
        "INSERT INTO Bids (Seller_Email, Listing_ID, Bidder_Email, Bid_Price) VALUES (?, ?, ?, ?)",
        (seller_email, listing_id, bidder_email, bid_price)
    )

    remaining = listing[1] - 1
    new_status = 2 if remaining == 0 else 1 # 2: sold, 1: still active

    # Decrement remaining bids and update status if max bids is reached 
    cursor.execute("""
        UPDATE Auction_Listings SET Remaining_Bids = ?, Status = ?
        WHERE Seller_Email = ? AND Listing_ID = ?
    """, (remaining, new_status, seller_email, listing_id))

    conn.commit()
    conn.close()

    # If auction just ended (max bids reached), go to result page
    if new_status == 2:
        return redirect(url_for("auction_result",
            seller_email=seller_email, listing_id=listing_id))

    # Otherwise back to detail page with success (listing is active)
    return redirect(url_for("auction_detail",
        seller_email=seller_email, listing_id=listing_id,
        feedback="Bid placed!", type="success"))

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

@app.route("/submit_rating", methods=["POST"])
def submit_rating():
    if 'email' not in session:
        return redirect(url_for("login"))

    bidder = session['email']
    seller = request.form.get("seller_email", "").strip()
    listing = request.form.get("listing_id", "").strip()

    try:
        rating = int(request.form.get("rating", "").strip())
    except ValueError:
        return redirect(url_for(
            "confirmation_page",
            seller_email=seller,
            listing_id=listing,
            rating_feedback="Please choose a rating from 1 to 5.",
            rating_feedback_type="error"
        ))

    if rating < 1 or rating > 5:
        return redirect(url_for(
            "confirmation_page",
            seller_email=seller,
            listing_id=listing,
            rating_feedback="Please choose a rating from 1 to 5.",
            rating_feedback_type="error"
        ))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ensure transaction exists
    cursor.execute("""
        SELECT *
        FROM Transactions
        WHERE Seller_Email=? AND Listing_ID=? AND Buyer_Email=?
    """, (seller, listing, bidder))

    if not cursor.fetchone():
        conn.close()
        return redirect(url_for("bidder_dashboard"))

    rating_desc_map = {
        1: "Bad",
        2: "Not Bad",
        3: "Okay",
        4: "Good",
        5: "Awesome",
    }
    rating_desc = rating_desc_map.get(rating, "Okay")
    rating_date = datetime.now(timezone.utc).date().isoformat()

    # update an existing rating for this listing, or insert a new one
    cursor.execute("""
        SELECT 1
        FROM Ratings
        WHERE Bidder_email=? AND Seller_Email=? AND Listing_ID=?
    """, (bidder, seller, listing))

    if cursor.fetchone():
        cursor.execute("""
            UPDATE Ratings
            SET Date = ?, Rating = ?, Rating_Desc = ?
            WHERE Bidder_email = ? AND Seller_Email = ? AND Listing_ID = ?
        """, (rating_date, rating, rating_desc, bidder, seller, listing))
        feedback = "Your rating was updated."
    else:
        cursor.execute("""
            INSERT INTO Ratings (Bidder_email, Seller_Email, Listing_ID, Date, Rating, Rating_Desc)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (bidder, seller, listing, rating_date, rating, rating_desc))
        feedback = "Thanks for rating this seller."

    conn.commit()
    conn.close()
    return redirect(url_for(
        "confirmation_page",
        seller_email=seller,
        listing_id=listing,
        rating_feedback=feedback,
        rating_feedback_type="success"
    ))

if __name__ == "__main__":
    app.run(debug=True)
