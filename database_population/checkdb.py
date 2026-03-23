import sqlite3
import csv
import hashlib

def hash_password(plain: str) -> str:
    return hashlib.sha256(str(plain).encode()).hexdigest()

# 1. Connected to the correct folder
conn = sqlite3.connect("nittany_auction.db")
#conn.execute("PRAGMA foreign_keys = ON")

with open("schema.sql", "r", encoding="utf-8") as f:
    conn.executescript(f.read())

cur = conn.cursor()

# ---------- 1. USERS ----------
with open("Users.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        # Strip invisible spaces from both the email and password
        email = row[0].strip()
        hashed_pw = hash_password(row[1].strip())
        cur.execute("INSERT INTO Users (email, password) VALUES (?, ?)", (email, hashed_pw))

# ---------- 2. BIDDERS ----------
with open("Bidders.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]
        cur.execute("INSERT INTO Bidders (email, first_name, last_name, age, home_address_id, major) VALUES (?, ?, ?, ?, ?, ?)", cleaned_row)

# ---------- 3. SELLERS ----------
with open("Sellers.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]
        cur.execute("INSERT INTO Sellers (email, bank_routing_number, bank_account_number, balance) VALUES (?, ?, ?, ?)", cleaned_row)

# ---------- 4. HELPDESK ----------
with open("Helpdesk.csv", "r", encoding="utf-8-sig") as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        cleaned_row = [item.strip() for item in row]
        cur.execute("INSERT INTO Helpdesk (email, position) VALUES (?, ?)", cleaned_row)

# ---------- 5. Local_Vendors ----------
with open("Local_Vendors.csv", "r", encoding="utf-8-sig") as file:
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
