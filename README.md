# NittanyAuction
Nittany Auction codebase

This website is created for the Nittany Auction. The user interface allows users to log in using registered information in the database to access the auction website. 

Features:

- A main login page that uses bootstrap that securely collects user login information with error handling in the event of invalid login details.
- Authentication system using hashing for passwords using SHA-256.
- Role based routing, successful logins will redirect users to specific pages based on their user status.
- Functions like logout


----------------------------------------------WEB PROGRAMMING EXERCISE STUFF BELOW (USE AS TEMPLATE OR DELETE) ------------------------------------------------------------



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
