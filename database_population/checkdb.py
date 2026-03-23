import sqlite3
import csv

conn = sqlite3.connect("nittany_auction.db")
conn.execute("PRAGMA foreign_keys = ON")

with open("schema.sql", "r", encoding="utf-8") as f:
    conn.executescript(f.read())

cur = conn.cursor()

with open("dataset/Users.csv", "r", encoding="utf-8") as file:
    reader = csv.reader(file)
    next(reader)

    for row in reader:
        cur.execute(
            "INSERT INTO Users (email, password) VALUES (?, ?)",
            row
        )

------ 

with open("dataset/Bidders.csv", "r", encoding="utf-8") as file:
    reader = csv.reader(file)
    next(reader)

    for row in reader:
        cur.execute(
            "INSERT INTO Bidders (email, first_name, last_name, age, home_address_id, major) VALUES (?, ?, ?, ?, ?, ?)",
            row
        )

with open("dataset/Sellers.csv", "r", encoding="utf-8") as file:
    reader = csv.reader(file)
    next(reader)

    for row in reader:
        cur.execute(
            "INSERT INTO Sellers (email, bank_routing_number, bank_account_number, balance) VALUES (?, ?, ?, ?)",
            row
        )


with open("dataset/Helpdesk.csv", "r", encoding="utf-8") as file:
    reader = csv.reader(file)
    next(reader)

    for row in reader:
        cur.execute(
            "INSERT INTO Helpdesk (email, Position) VALUES (?, ?)",
            row
        )

--------
conn.commit()

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:")
for row in cur.fetchall():
    print(row[0])

cur.execute("SELECT COUNT(*) FROM Users;")
print("Users count:", cur.fetchone()[0])

cur.execute("SELECT * FROM Users LIMIT 5;")
print("Sample users:")
for row in cur.fetchall():
    print(row)

conn.close()
