PRAGMA foreign_keys = ON;

-- DROP TABLES
DROP TABLE IF EXISTS Local_Vendors;
DROP TABLE IF EXISTS Sellers;
DROP TABLE IF EXISTS Helpdesk;
DROP TABLE IF EXISTS Bidders;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Address;
DROP TABLE IF EXISTS Zipcode_Info;

-- ZIPCODE
CREATE TABLE Zipcode_Info (
    zipcode TEXT PRIMARY KEY,
    city TEXT NOT NULL,
    state_name TEXT NOT NULL
);

-- ADDRESS
CREATE TABLE Address (
    address_id TEXT PRIMARY KEY,
    zipcode TEXT NOT NULL,
    street_num TEXT NOT NULL,
    street_name TEXT NOT NULL,
    FOREIGN KEY (zipcode) REFERENCES Zipcode_Info(zipcode)
);

-- USERS
CREATE TABLE Users (
    email TEXT PRIMARY KEY,
    password TEXT NOT NULL
);

-- BIDDERS
CREATE TABLE Bidders (
    email TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    age INTEGER,
    phone_number TEXT,
    major TEXT,
    home_address_id TEXT,
    FOREIGN KEY (email) REFERENCES Users(email) ON DELETE CASCADE,
    FOREIGN KEY (home_address_id) REFERENCES Address(address_id)
);

-- HELPDESK
CREATE TABLE Helpdesk (
    email TEXT PRIMARY KEY,
    position TEXT,
    FOREIGN KEY (email) REFERENCES Users(email) ON DELETE CASCADE
);

-- SELLERS
CREATE TABLE Sellers (
    email TEXT PRIMARY KEY,
    bank_routing_number TEXT NOT NULL,
    bank_account_number TEXT NOT NULL,
    balance REAL DEFAULT 0,
    FOREIGN KEY (email) REFERENCES Users(email) ON DELETE CASCADE
);

-- LOCAL VENDORS
CREATE TABLE Local_Vendors (
    email TEXT PRIMARY KEY,
    business_name TEXT NOT NULL,
    business_address_id TEXT,
    customer_service_phone_number TEXT,
    FOREIGN KEY (email) REFERENCES Sellers(email) ON DELETE CASCADE,
    FOREIGN KEY (business_address_id) REFERENCES Address(address_id)
);