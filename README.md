# NittanyAuction
Nittany Auction codebase
This website is created for the Nittany Auction. The user interface allows users to log in using registered information in the database to access the auction website. 

Features:

A main page that includes the header "Hospital Patient Portal" with a description of the portal and its use cases. Aswell as having a dropdown menu to access specific forms.
There is a form that allows you to add a patient's first and last name, a unique identification number (pid) will be assigned to each patient using AUTOINCREMENT which provides unique ID numbers sequentially.
There is a form that allows you to delete a patients first and last name. Both forms also include the table with the current updated information of the patients in the database.
Included bootstrap modals which act as confirmation from the user incase they want to rethink their decision.

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
