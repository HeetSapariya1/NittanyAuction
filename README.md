# NittanyAuction
Nittany Auction codebase

This website is created for the Nittany Auction. The user interface allows users to register and log in for new accounts as well as existing accounts in the database, after authentication users will be able to access the auction website, and the webpage will be role-specific.

Authors:
Colin Lombardi
Sankeerth Mahesh
Heet Sapariya
Justin Huang

Features:

- Login and Registration System: A main login page that uses bootstrap that securely collects user login information with error handling in the event of invalid login details. A registration form that is specific to a user's role and will generate keys for the data to be updated in the database. An authentication system using hashing for passwords using SHA-256. Role-based routing: Successful logins will redirect users to specific pages based on their role.
- Profile Management: Users can view their profiles with the registered personal information and account information. Users can also update this information on their role-specific dashboard.
- Category Hierarchy & Product Search: Users can select specific categories to view particular listings, as well as filter and search by keywords and the status of a product, i.e., if it's a premium item. 
- Bidding: Bidders can view listings and place bids in real-time with a "My Bids" dashboard that will track the listings they are associated with. Rules will be enforced to promote bidder integrity, such as requiring a minimum bid, with dollar increments, and preventing consecutive bids. When maximum bids are reached for a listing, the system will evaluate the highest bid against the listing's reserve price to decide a winner and route them to a payment and review page.
- Sellers: Sellers can create listings that will have defined parameters like reserve price, limit on the number of bids, the category it belongs to, and its premium status. Sellers can filter their listings by category and status, including active, inactive, or sold. They can also pause or delete listings, which will be archived.
- Database Architecture: The Users table branches out to other roles "Bidders, "Sellers", "HelpDesk" and "Sellers" with cascading foreign keys. Local Vendors act as a weak entity that extends the "Sellers" table. Cascading deletion: When a user is removed, all associated account information, bids, and financial records will be wiped. Utilizes INSERT OR IGNORE logic to prevent duplicate information.

---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Organization:

The project is divided into 4 parts.

- README: which illustrates the background and process of the project.
- Backend: The main.py which is the core Python script that uses Flask and SQlite for routing, session management, and other various processes. Checkdb.py, which is used to initialize and populate the database.
- Frontend: Templates folder, which includes all the HTML files that handle the front-end of the website, stylized using Bootstrap/custom CSS.
- Database: SQLite schema that imposes different relationships. For example, Users, Bidders, Sellers, Local Vendors, and Helpdesk.

Instructions:

1. Download or clone the repository files; it should be all in one folder, and in your IDE of choice. Then open the project/folder.
2. Ensure that Python and Flask are all installed locally, either automatically or manually (example: pip install flask)
3. Locate checkdb.py and run it; this will initialize and populate the database. Then locate main.py to run the script to start the server. 
4. In the IDE's console, you should see a local URL. Once selected, the website should appear in your default browser. In our case its http://127.0.0.1:5000.
5. Begin by registering/creating a new account or logging in with existing credentials to start using the website and its many functions.
