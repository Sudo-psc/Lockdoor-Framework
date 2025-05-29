import os
import os
import datetime # For the Jinja filter
from flask import Flask, render_template
from src.plugin_framework_core import PluginManager
# Import the c2_views blueprint
from .c2_views import c2_bp 

app = Flask(__name__)

# Determine the project root directory to reliably find the 'plugins' folder
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
plugins_directory = os.path.join(project_root, "plugins")

# Initialize PluginManager
plugin_manager_instance = PluginManager()
plugin_manager_instance.discover_plugins(plugin_folder=plugins_directory)

# Attach PluginManager to the app context
app.plugin_manager = plugin_manager_instance

# Register C2 Blueprint
app.register_blueprint(c2_bp)

# Jinja filter for datetime formatting
def format_datetime(value, fmt='%Y-%m-%d %H:%M:%S'):
    if isinstance(value, (int, float)):
        try:
            return datetime.datetime.fromtimestamp(value).strftime(fmt)
        except ValueError: # Handle potential errors with timestamp conversion
            return "Invalid timestamp" 
    if isinstance(value, datetime.datetime): # If it's already a datetime object
        return value.strftime(fmt)
    return value # Return as is if not a recognized type or already formatted

app.jinja_env.filters['datetimeformat'] = format_datetime


@app.route('/')
def index():
    return render_template('index.html', title='Welcome to Lockdoor Framework')

@app.route('/plugins')
def list_plugins_route():
    # Use list_plugins_with_details() from the app's plugin_manager
    plugins_with_details = app.plugin_manager.list_plugins_with_details()
    return render_template('plugins.html', title='Available Plugins', plugins_data=plugins_with_details)

if __name__ == '__main__':
    # This allows running the app directly from src/web_panel/app.py for development
    # However, the run.py at the project root is the preferred way to start.
    app.run(debug=True, host='0.0.0.0', port=5000)
