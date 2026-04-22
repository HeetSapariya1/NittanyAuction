import sqlite3
import csv
import hashlib

def hash_password(plain: str) -> str:
    return hashlib.sha256(str(plain).encode()).hexdigest()

# Connect to SQLite DB and enable foreign key constraints
conn = sqlite3.connect("nittany_auction.db")
conn.execute("PRAGMA foreign_keys = ON")

# read from the existing schem.sql and execute it to create the tables
with open("schema.sql", "r", encoding="utf-8") as f: 
    conn.executescript(f.read())

cur = conn.cursor()

# read the zipcode info and insert into db 
with open("dataset/Zipcode_Info.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]
        cur.execute(
            "INSERT INTO Zipcode_Info (zipcode, city, state_name) VALUES (?, ?, ?)",
            cleaned_row
        )

with open("dataset/Address.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]

        address_id = cleaned_row[0] if cleaned_row[0] != "" else None
        zipcode = cleaned_row[1]
        street_num = cleaned_row[2]
        street_name = cleaned_row[3]

        cur.execute(
            "INSERT INTO Address (address_id, zipcode, street_num, street_name) VALUES (?, ?, ?, ?)",
            (address_id, zipcode, street_num, street_name)
        )

with open("dataset/Users.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        email = row[0].strip()
        hashed_pw = hash_password(row[1].strip())
        cur.execute("INSERT INTO Users (email, password) VALUES (?, ?)", (email, hashed_pw))

with open("dataset/Bidders.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]

        email = cleaned_row[0]
        first_name = cleaned_row[1]
        last_name = cleaned_row[2]
        age = int(cleaned_row[3]) if cleaned_row[3] != "" else None
        home_address_id = cleaned_row[4] if cleaned_row[4] != "" else None
        major = cleaned_row[5] if cleaned_row[5] != "" else None
        phone_number = None

        cur.execute("""
            INSERT INTO Bidders
            (email, first_name, last_name, age, phone_number, major, home_address_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (email, first_name, last_name, age, phone_number, major, home_address_id))

with open("dataset/Sellers.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]
        cur.execute("INSERT INTO Sellers (email, bank_routing_number, bank_account_number, balance) VALUES (?, ?, ?, ?)", cleaned_row)

with open("dataset/Helpdesk.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]

        email = cleaned_row[0]
        position = cleaned_row[1]

        cur.execute("SELECT 1 FROM Users WHERE email = ?", (email,))
        if cur.fetchone():
            cur.execute(
                "INSERT INTO Helpdesk (email, position) VALUES (?, ?)",
                (email, position)
            )
        else:
            print("email not in Users  ", email)

with open("dataset/Local_Vendors.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]
        cur.execute("INSERT INTO Local_Vendors (email, business_name, business_address_id, customer_service_phone_number) VALUES (?, ?, ?, ?)", cleaned_row)

# populate categories with category name and parent category (if applicable) from the Categories.csv file. 
with open("dataset/Categories.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        parent = row[0].strip()
        name   = row[1].strip()
        cur.execute("INSERT INTO Categories (category_name, parent_category) VALUES (?, ?)",(name, parent))

with open("dataset/Auction_Listings.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)
    for row in reader:
        seller_email = row["Seller_Email"].strip()
        listing_id = int(row["Listing_ID"].strip())
        category = row["Category"].strip()
        auction_title = row["Auction_Title"].strip()
        product_name = row["Product_Name"].strip()
        product_description = row["Product_Description"].strip() or None
        quantity = int(row["Quantity"].strip()) if row["Quantity"].strip() else 1

        # CSV stores prices with formatting like "$50 " or "5,500".
        reserve_price = float(
            row["Reserve_Price"].replace("$", "").replace(",", "").strip()
        )
        max_bids = int(row["Max_bids"].strip())
        status = int(row["Status"].strip()) if row["Status"].strip() else 1

        cur.execute("""
            INSERT INTO Auction_Listings (
                Seller_Email,
                Listing_ID,
                Category,
                Auction_Title,
                Product_Name,
                Product_Description,
                Premium_Item,
                Quantity,
                Reserve_Price,
                Max_Bids,
                Remaining_Bids,
                Status,
                Removal_Reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            seller_email,
            listing_id,
            category,
            auction_title,
            product_name,
            product_description,
            0,
            quantity,
            reserve_price,
            max_bids,
            max_bids,
            status,
            None
        ))

conn.commit()

conn.close()
print("\nDatabase ready")
