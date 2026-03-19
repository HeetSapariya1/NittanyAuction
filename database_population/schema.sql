-- 1. Location Data
-- Initial DB Schema had Street, City, State, and Zipcode under Address attribute with a relationship to Bidders. 
-- Provided Schema states the Zipcode is a unique table that has a relation to Address

CREATE TABLE Zipcode_Info (
    zipcode CHAR(10) PRIMARY KEY,
    city CHAR(100) NOT NULL,
    state CHAR(50) NOT NULL
);

CREATE TABLE Address (
    address_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    zipcode CHAR(10) NOT NULL,
    street_num CHAR(20) NOT NULL,
    street_name CHAR(255) NOT NULL,
    FOREIGN KEY (zipcode) REFERENCES Zipcode_Info(zipcode)
);

-- 2. Base User Table (
CREATE TABLE Users (
    email CHAR(255) PRIMARY KEY,
    password CHAR(255)
);


-------

CREATE TABLE Bidders (
    email CHAR(255) PRIMARY KEY,
    first_name CHAR(255),
    last_name CHAR(255),
    age INTEGER,
    home_address_id CHAR(255),
    major CHAR(255)
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
    Position CHAR(255),
    FOREIGN KEY (email) REFERENCES Users(email)
);

CREATE TABLE Local_Vendors (
    Email CHAR(255) PRIMARY KEY,
    Business_Name CHAR(255),
    Business_Address_ID CHAR(255),
    Customer_Service_Phone_Number CHAR(255),
    FOREIGN KEY (Email) REFERENCES Users(email)
);
    

