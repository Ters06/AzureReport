# This file is the new entry point to run the application.
from app import create_app

# Create an instance of the Flask application
app = create_app()

if __name__ == "__main__":
    # Run the app in debug mode
    app.run(debug=True)
