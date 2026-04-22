PRAGMA foreign_keys = ON;

-- DROP TABLES 
DROP TABLE IF EXISTS Local_Vendors;
DROP TABLE IF EXISTS Sellers;
DROP TABLE IF EXISTS Helpdesk;
DROP TABLE IF EXISTS Bidders;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Address;
DROP TABLE IF EXISTS Zipcode_Info;
DROP TABLE IF EXISTS Bids;
DROP TABLE IF EXISTS Transactions;
DROP TABLE IF EXISTS Auction_Listings;
DROP TABLE IF EXISTS Listing_Removals;
DROP TABLE IF EXISTS Categories;
DROP TABLE IF EXISTS Credit_Cards;
DROP TABLE IF EXISTS Ratings;

-- ZIPCODE
-- maps zip code to its specific city and state, which can be used to populate the address table and provide location information for users and vendors.
CREATE TABLE Zipcode_Info (
    zipcode TEXT PRIMARY KEY, -- identifies zip code associated to city and state
    city TEXT NOT NULL,
    state_name TEXT NOT NULL
);

-- ADDRESS
-- used by Bidders and Local Vendors 
CREATE TABLE Address (
    address_id TEXT PRIMARY KEY, -- uniquely identify the address
    zipcode TEXT NOT NULL, -- must have a valid zipcode that exists in the table 
    street_num TEXT NOT NULL, 
    street_name TEXT NOT NULL,
    FOREIGN KEY (zipcode) REFERENCES Zipcode_Info(zipcode) -- ensure zipcode is in zipcode table when inserting
);

-- USERS
-- creates login credentials for bidders, sellers, helpdesk staff, and local vendors
-- each user has a unique email across all roles 
-- password associated to each email and is hashed 
CREATE TABLE Users (
    email TEXT PRIMARY KEY,
    password TEXT NOT NULL
);

-- BIDDERS
CREATE TABLE Bidders (
    email TEXT PRIMARY KEY, -- unique email for each bidder
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    Premium_User INTEGER DEFAULT 0 CHECK (Premium_User IN (0, 1)),
    age INTEGER,
    phone_number TEXT,
    major TEXT,
    home_address_id TEXT, -- reference to bidder address
    FOREIGN KEY (email) REFERENCES Users(email) ON DELETE CASCADE, -- deleting a user removes the bidder as well
    FOREIGN KEY (home_address_id) REFERENCES Address(address_id)
);

-- HELPDESK
CREATE TABLE Helpdesk (
    email TEXT PRIMARY KEY, -- unique email for each helpdesk staff member
    position TEXT,
    FOREIGN KEY (email) REFERENCES Users(email) ON DELETE CASCADE -- deleting a user removes the helpdesk staff member as well
);

-- SELLERS
CREATE TABLE Sellers (
    email TEXT PRIMARY KEY, -- unique email for each seller
    bank_routing_number TEXT NOT NULL,
    bank_account_number TEXT NOT NULL,
    balance REAL DEFAULT 0,
    FOREIGN KEY (email) REFERENCES Users(email) ON DELETE CASCADE -- deleting a user removes the seller as well
);

-- LOCAL VENDORS (weak entity of Sellers)
CREATE TABLE Local_Vendors (    
    email TEXT PRIMARY KEY, -- constrained to Sellers email, so each local vendor is also a seller
    business_name TEXT NOT NULL,
    business_address_id TEXT,
    customer_service_phone_number TEXT,
    FOREIGN KEY (email) REFERENCES Sellers(email) ON DELETE CASCADE, -- deleting a seller removes the local vendor as well
    FOREIGN KEY (business_address_id) REFERENCES Address(address_id) -- ensures valid address id exists s
);

CREATE TABLE Credit_Cards (
    credit_card_num TEXT PRIMARY KEY,
    card_type TEXT NOT NULL,
    expire_month INTEGER NOT NULL,
    expire_year INTEGER NOT NULL,
    security_code INTEGER NOT NULL,
    Owner_email TEXT NOT NULL,
    FOREIGN KEY (Owner_email) REFERENCES Users(email)
);

CREATE TABLE Ratings (
    Bidder_email TEXT NOT NULL,
    Seller_email TEXT NOT NULL,
    Date TEXT NOT NULL,
    Rating INTEGER CHECK (Rating BETWEEN 1 AND 5), -- rating must be between 1 and 5
    Rating_Desc TEXT,
    PRIMARY KEY( Bidder_email, Seller_email ),
    FOREIGN KEY (Bidder_email) REFERENCES Bidders(email),
    FOREIGN KEY (Seller_email) REFERENCES Sellers(email)
);

-- CATEGORIES
-- split into parent_category and category_name to allow for hierarchical categories like Sports -> Baseball
CREATE TABLE Categories (
    category_name TEXT PRIMARY KEY, -- unique name for each category
    parent_category TEXT
);
    
-- AUCTION LISTINGS
CREATE TABLE Auction_Listings (
    Seller_Email TEXT NOT NULL,
    Listing_ID INTEGER NOT NULL,
    Category TEXT NOT NULL,
    Auction_Title TEXT NOT NULL,
    Product_Name TEXT NOT NULL,
    Product_Description TEXT,
    Premium_Item INTEGER DEFAULT 0 CHECK (Premium_Item IN (0, 1)),
    Quantity INTEGER DEFAULT 1,
    Reserve_Price REAL NOT NULL,
    Max_Bids INTEGER NOT NULL,
    Remaining_Bids INTEGER NOT NULL CHECK (Remaining_Bids >= 0),
    Status INTEGER DEFAULT 1 CHECK (Status IN (0, 1, 2)), -- 0 not active , 1 active 2 sold
    Removal_Reason TEXT,
    PRIMARY KEY (Seller_Email, Listing_ID), -- composite primary key to allow sellers to have multiple listings 
    FOREIGN KEY (Seller_Email) REFERENCES Sellers(email) ON DELETE CASCADE, -- deleting a seller removes the listing as well
    FOREIGN KEY (Category) REFERENCES Categories(category_name) -- ensures category exists in categories table when inserting a listing
);

CREATE TABLE Listing_Removals (
    Removal_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Seller_Email TEXT NOT NULL,
    Listing_ID INTEGER NOT NULL,
    Auction_Title TEXT NOT NULL,
    Removed_Status INTEGER NOT NULL,
    Removal_Reason TEXT,
    Removed_At TEXT NOT NULL
);

-- BIDS
CREATE TABLE Bids (
    Bid_ID INTEGER PRIMARY KEY AUTOINCREMENT, -- bid id to uniquely identify each bid
    Seller_Email TEXT NOT NULL,
    Listing_ID INTEGER NOT NULL,
    Bidder_Email TEXT NOT NULL,
    Bid_Price REAL NOT NULL,
    FOREIGN KEY (Seller_Email, Listing_ID) REFERENCES Auction_Listings(Seller_Email, Listing_ID) ON DELETE CASCADE, -- deleting a seller or listing removes the bid
    FOREIGN KEY (Bidder_Email) REFERENCES Bidders(email) 
);

-- TRANSACTIONS
CREATE TABLE Transactions (
    Transaction_ID INTEGER PRIMARY KEY AUTOINCREMENT, -- transaction id to uniquely identify each transaction
    Seller_Email TEXT NOT NULL,
    Listing_ID INTEGER NOT NULL,
    Buyer_Email TEXT NOT NULL,
    Date TEXT NOT NULL,
    Payment REAL NOT NULL,
    FOREIGN KEY (Seller_Email, Listing_ID) REFERENCES Auction_Listings(Seller_Email, Listing_ID) ON DELETE CASCADE, -- deeleting a seller or listing removes the transaction 
    FOREIGN KEY (Buyer_Email) REFERENCES Bidders(email) 
);


