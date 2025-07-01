# **Instructions for Setup and Execution**

### **1. Prerequisites:**

* You need to have Python 3 installed on your system.
* You will need to install the required Python packages. Open your terminal or command prompt, navigate to the project folder, and run:
    ```bash
    pip install -r requirements.txt
    ```

### **2. File Structure:**

* Create a main folder for this project (e.g., "AzureDynamicReport").
* Inside this folder, place the Python files:
    * `app.py`
    * `seeder.py`
    * `models.py`
    * `requirements.txt`
* Create a subfolder named `templates`.
* Save all the HTML files into this `templates` folder.
* Create another subfolder named `static`. Inside `static`, create a `js` folder.
    * Save `main.js` into the `static/js` folder.
* Place your client's CSV files in the main project folder.

Your folder structure should now look like this:

/AzureReport  
|-- app/
|   |-- __init__.py
|   |-- models.py
|   |-- context_processors.py
|   |-- routes/
|   |   |-- __init__.py
|   |   |-- api.py
|   |   |-- main.py
|   |   |-- recommendations.py
|   |   |-- vms.py
|   |-- static/
|   |   |-- js/
|   |       |-- charts.js
|   |       |-- tables.js
|   |       |-- ui.js
|   |-- templates/
|       |-- (all .html files)
|-- run.py
|-- seeder.py
|-- requirements.txt
|-- Advisor\_\*.csv  
|-- AzureVirtualMachines.csv  
|-- AzurevirtualMachineScaleSets.csv  
|-- Subscriptions.csv  
|-- Azureresourcegroups.csv
|-- <Other Azure Service>.csv

### **3. Run the Application:**

* Open your terminal or command prompt and navigate to the "AzureDynamicReport" folder.
* **Step 1: Create and seed the database (Run this for each new client)**
    ```bash
    python seeder.py "<Client Name>"
    ```
* **Step 2: Start the web server**
    ```bash
    python app.py
    ```
* **Step 3: View the report**
    Open your web browser and go to: `http://127.0.0.1:5000`