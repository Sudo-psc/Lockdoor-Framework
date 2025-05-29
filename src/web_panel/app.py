import os
from flask import Flask, render_template
from src.plugin_framework_core import PluginManager

app = Flask(__name__)

# Determine the project root directory to reliably find the 'plugins' folder
# __file__ is src/web_panel/app.py
# os.path.dirname(__file__) is src/web_panel
# os.path.dirname(os.path.dirname(__file__)) is src
# os.path.dirname(os.path.dirname(os.path.dirname(__file__))) is the project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
plugins_directory = os.path.join(project_root, "plugins")

plugin_manager = PluginManager()
plugin_manager.discover_plugins(plugin_folder=plugins_directory)

@app.route('/')
def index():
    return render_template('index.html', title='Welcome to Lockdoor Framework')

@app.route('/plugins')
def list_plugins_route():
    # Use list_plugins_with_details() to get instances and actions
    plugins_with_details = plugin_manager.list_plugins_with_details()
    # The template will expect a dictionary where keys are plugin names
    # and values are dicts containing 'instance' and 'actions'.
    # list_plugins_with_details() already returns this format.
    return render_template('plugins.html', title='Available Plugins', plugins_data=plugins_with_details)

if __name__ == '__main__':
    # This allows running the app directly from src/web_panel/app.py for development
    # However, the run.py at the project root is the preferred way to start.
    app.run(debug=True, host='0.0.0.0', port=5000)
