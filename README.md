# NittanyAuction
Nittany Auction codebase

This website is created for the Nittany Auction. The user interface allows users to log in using registered information in the database to access the auction website. 

Features:

- A main login page that uses bootstrap that securely collects user login information with error handling in the event of invalid login details.
- Authentication system using hashing for passwords using SHA-256.
- Role based routing, successful logins will redirect users to specific pages based on their user status.
- Functions like logout



---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Organization:

The project is divided into 4 parts.

README which illustrates the background and process of the project.
The app.py which is the Python script that uses Flask and SQlite for updating patient information
Templates folder which includes all the HTML files which handle the front-end of the website, the index.html which handles the main portal, input.html which handles adding patients, delete.html which handles deleting patients.
database.db which stores all patient information

Instructions:

Download the files, it should be all in one folder and in your IDE of choice open the project/folder.
Make sure Python, Flask and everything else is installed.
Locate app.py and run it which in our case is under starter_code_431w and press the run button which is green on the top right.
In the console you should see a URL click on that and the website should pop up, in our case its http://127.0.0.1:5000
You should be able to try out the functions of the website


Phase 2 Checkpoint 1: 

So Far Nittany Auction foucses mainly on User Roles such as: Seller, Bidder, and Helpdesk
  1 - > The main Login Page allows users to enter their credentials based of their specific role
  2 - > Depending on their role, users will be directed to our temperary Seller, Bidder, or Helpdesk Dashboard
  3 - > Ontop of being dircted to the dashboards, authentiction will take place as passwords are hashed using SHA-256 function and will be stored in the Db


Databse - The app uses a local SQLite database locasted at database_population/nittany_auction.db

The Database schema follows a role based hierarchy that share a USer table and slowly ectnded to a role specific table using cascading forgien keys. ZipCode and Adress are their own enities that stores location data for each user. Bidders, Sellers, Helpdesk all extend user while Helpdesk extends seller as it is identified with a no- LSU email in the database.

Key design functions
  1. Cascading deletion: When a user is removed, it automatically gets rid of their row
  2. Local vendors inherit from sillers and have their own data from sellers table
  3. Passwords are stored in hex strings
  4. Addresses can be shared across tables
