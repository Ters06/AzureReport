# **Instructions for Setup and Execution**

### **1\. Prerequisites:**

* You need to have Python 3 installed on your system.  
* You will need to install Flask. Open your terminal or command prompt and run:  
  pip install Flask

### **2\. File Structure:**

* Create a main folder for this project (e.g., "AzureDynamicReport").  
* Inside this folder, save the Python files:  
  * app.py  
  * seeder.py  
* Create a subfolder named templates.  
* Save all the HTML files into this templates folder.  
* **Create another subfolder named static**. Inside static, create two more folders: css and js.  
  * Save style.css into the static/css folder.  
  * Save main.js into the static/js folder.  
* Place your client's CSV files in the main project folder.

Your folder structure should now look like this:

/AzureDynamicReport  
|-- app.py  
|-- seeder.py  
|-- Advisor\_\*.csv  
|-- AzureVirtualMachines.csv  
|-- AzurevirtualMachineScaleSets.csv  
|-- Subscriptions.csv  
|-- Azureresourcegroups.csv  
|-- /static  
|   |-- /css  
|   |   |-- style.css  
|   |-- /js  
|       |-- main.js  
|-- /templates  
    |-- layout.html  
    |-- index.html  
    |-- vms.html  
    |-- vm\_detail.html  
    |-- vmss.html  
    |-- vmss\_detail.html  
    |-- recommendations.html

### **3\. Run the Application:**

* Open your terminal or command prompt and navigate to the "AzureDynamicReport" folder.  
* **Step 1: Create the database (Run this for each new client)**  
  python seeder.py "<Client Name>"

* **Step 2: Start the web server**  
  python app.py

* Step 3: View the report  
  Open your web browser and go to: http://127.0.0.1:5000