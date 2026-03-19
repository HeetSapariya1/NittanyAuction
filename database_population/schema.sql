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


