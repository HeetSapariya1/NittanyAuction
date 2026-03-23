-- 1. Location Data
-- Initial DB Schema had Street, City, State, and Zipcode under Address attribute with a relationship to Bidders. 
-- Provided Schema states the Zipcode is a unique table that has a relation to Address

CREATE TABLE Zipcode_Info (
    zipcode CHAR(10) PRIMARY KEY,
    city CHAR(100) NOT NULL,
    state_name CHAR(50) NOT NULL
);

CREATE TABLE Address (
    address_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    zipcode CHAR(10) NOT NULL,
    street_num CHAR(20) NOT NULL,
    street_name CHAR(255) NOT NULL,
    FOREIGN KEY (zipcode) REFERENCES Zipcode_Info(zipcode)
);

-- 2. Base User Table (HelpDesk, Bidders, and Sellers are part of Users)
CREATE TABLE Users (
    email CHAR(255) PRIMARY KEY,
    password char(255) NOT NULL
);

-- 4. Bidders 
CREATE TABLE Bidders (
    email CHAR(255) PRIMARY KEY,
    first_name CHAR(255) NOT NULL,
    last_name CHAR(255) NOT NULL,
    age INTEGER,
    phone_number CHAR(255), 
    major CHAR(255),
    home_address_id INTEGER,
    FOREIGN KEY (email) REFERENCES Users(email) ON DELETE CASCADE, -- if a user is removed, delete it from bidders
    FOREIGN KEY (home_address_id) REFERENCES Address(address_ID) -- many-to-one relationship, such that several bidders can have the same address. This also maintains data integrity and rejects bidders without valid addresses.
);

-- 5. Helpdesk
CREATE TABLE Helpdesk (
    email CHAR(255) PRIMARY KEY,
    staff_id CHAR(50) UNIQUE ,
    staff_name CHAR(255),
    position CHAR(255),
    hired_date DATE,
    FOREIGN KEY (email) REFERENCES Users(email) ON DELETE CASCADE -- if a user is removed, delete it from HelpDesk
);

-- 6. Sellers 
CREATE TABLE Sellers (
    email CHAR(255) PRIMARY KEY,
    bank_routing_number CHAR(255) NOT NULL,
    bank_account_number CHAR(255) NOT NULL,
    balance DECIMAL(10, 2) DEFAULT 0.00,
    FOREIGN KEY (email) REFERENCES Users(email) ON DELETE CASCADE -- if a user is removed, delete it from Sellers
);

-- 7. Local Vendors (weak entity relationship with Sellers)
CREATE TABLE Local_Vendors (
    email CHAR(255) PRIMARY KEY,
    business_name CHAR(255) NOT NULL,
    ein CHAR(255) UNIQUE,      -- unique identifiier for local vendors
    customer_service_phone CHAR(255),
    business_address_id INTEGER,
    FOREIGN KEY (email) REFERENCES Sellers(email) ON DELETE CASCADE, -- if a user is removed from Sellers, delete it from local_vendors
    FOREIGN KEY (business_address_id) REFERENCES Address(address_ID) -- many-to-one relationship, such that several local vendors can have the same address.
);

---- 
CREATE TABLE Bidders (
    email CHAR(255) PRIMARY KEY,
    first_name CHAR(255),
    last_name CHAR(255),
    age INTEGER,
    home_address_id CHAR(255),
    major CHAR(255),
    FOREIGN KEY (email) REFERENCES Users(email)
);

CREATE TABLE Sellers (
    email CHAR(255) PRIMARY KEY,
    bank_routing_number CHAR(255),
    bank_account_number CHAR(255),
    balance INTEGER,
    FOREIGN KEY (email) REFERENCES Users(email)
);

CREATE TABLE Helpdesk (
    email CHAR(255) PRIMARY KEY,
    position CHAR(255),
    FOREIGN KEY (email) REFERENCES Users(email)
);

CREATE TABLE Local_Vendors (
    Email CHAR(255) PRIMARY KEY,
    Business_Name CHAR(255),
    Business_Address_ID CHAR(255),
    Customer_Service_Phone_Number CHAR(255),
    FOREIGN KEY (Email) REFERENCES Users(email)
);
    

