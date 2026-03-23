import sqlite3
import csv
import hashlib

def hash_password(plain: str) -> str:
    return hashlib.sha256(str(plain).encode()).hexdigest()

# 1. Connected to the correct folder
conn = sqlite3.connect("nittany_auction.db")
conn.execute("PRAGMA foreign_keys = ON")

with open("schema.sql", "r", encoding="utf-8") as f:
    conn.executescript(f.read())

cur = conn.cursor()

# ---------- 0. ZIPCODE_INFO ----------
with open("dataset/Zipcode_Info.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]
        cur.execute(
            "INSERT INTO Zipcode_Info (zipcode, city, state_name) VALUES (?, ?, ?)",
            cleaned_row
        )

# ---------- 0.5 ADDRESS ----------
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

# ---------- 1. USERS ----------
with open("dataset/Users.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        # Strip invisible spaces from both the email and password
        email = row[0].strip()
        hashed_pw = hash_password(row[1].strip())
        cur.execute("INSERT INTO Users (email, password) VALUES (?, ?)", (email, hashed_pw))

# ---------- 2. BIDDERS ----------
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

# ---------- 3. SELLERS ----------
with open("dataset/Sellers.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]
        cur.execute("INSERT INTO Sellers (email, bank_routing_number, bank_account_number, balance) VALUES (?, ?, ?, ?)", cleaned_row)

# ---------- 4. HELPDESK ----------
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
            print("Skipped Helpdesk row, email not in Users:", email)

# ---------- 5. Local_Vendors ----------
with open("dataset/Local_Vendors.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]
        cur.execute("INSERT INTO Local_Vendors (email, business_name, business_address_id, customer_service_phone_number) VALUES (?, ?, ?, ?)", cleaned_row)


conn.commit()

# --- Debugging Prints ---
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables successfully built:")
for row in cur.fetchall():
    print(f"- {row[0]}")

cur.execute("SELECT COUNT(*) FROM Users;")
print("\nTotal Users inserted:", cur.fetchone()[0])

conn.close()
print("\nDatabase is completely scrubbed, populated, and ready for Flask!")
