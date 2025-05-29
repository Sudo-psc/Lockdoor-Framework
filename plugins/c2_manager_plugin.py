import os
import ssl
import threading
import time # for timestamps
import uuid # for agent_id
from http.server import HTTPServer, BaseHTTPRequestHandler
# from socketserver import ThreadingMixIn # For concurrent requests if needed
import json # For C2 communication

from src.plugin_framework_core.plugin_interface import LockdoorPlugin, Action, ActionParameter
from typing import List, Dict, Any, Optional


# Define the handler class before C2ManagerPlugin or ensure it's correctly scoped/passed.
class SimpleC2HTTPHandler(BaseHTTPRequestHandler):
    # Store a reference to the plugin instance to interact with its data
    # This is set by the handler_factory in C2ManagerPlugin
    plugin_manager_ref: 'C2ManagerPlugin' 

    def __init__(self, plugin_ref: 'C2ManagerPlugin', *args, **kwargs):
        self.plugin_manager_ref = plugin_ref
        super().__init__(*args, **kwargs)

    def _send_response(self, status_code, data=None, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()
        if data:
            if isinstance(data, str):
                self.wfile.write(data.encode('utf-8'))
            else: # Assume JSON serializable
                self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_body_bytes = self.rfile.read(content_length)
        
        try:
            post_data = json.loads(post_body_bytes.decode('utf-8')) if post_body_bytes else {}
        except json.JSONDecodeError:
            self._send_response(400, {"error": "Invalid JSON data."})
            return

        client_ip, _ = self.client_address

        if self.path == '/register':
            agent_id = self.plugin_manager_ref._register_new_agent(client_ip, post_data)
            self._send_response(200, {"agent_id": agent_id, "status": "registered"})
            print(f"[C2 Listener] New agent registered: {agent_id} from {client_ip}")

        elif self.path == '/beacon':
            agent_id = post_data.get('agent_id')
            if not agent_id:
                self._send_response(400, {"error": "Missing agent_id in beacon."})
                return
            
            if self.plugin_manager_ref._agent_beaconed(agent_id, client_ip):
                command = self.plugin_manager_ref._get_pending_command(agent_id)
                if command:
                    self._send_response(200, {"command": command, "status": "command_pending"})
                else:
                    self._send_response(200, {"status": "ok", "message": "beacon_received"})
            else:
                self._send_response(404, {"error": f"Agent {agent_id} not recognized."})
        
        elif self.path == '/cmd_output':
            agent_id = post_data.get('agent_id')
            command_id = post_data.get('command_id') # Assuming agent sends back a command_id
            output = post_data.get('output')

            if not agent_id or output is None or command_id is None: # output can be empty string
                self._send_response(400, {"error": "Missing agent_id, command_id, or output."})
                return

            if self.plugin_manager_ref._store_command_output(agent_id, command_id, output):
                 self._send_response(200, {"status": "output_received"})
            else:
                self._send_response(404, {"error": f"Agent {agent_id} or command_id {command_id} not found or invalid."})

        else:
            self._send_response(404, {"error": "Endpoint not found."})

    def do_GET(self): # Optional, for simple check
        if self.path == '/health':
            self._send_response(200, "Listener is alive.", content_type='text/plain')
        else:
            self._send_response(404, "Not Found.", content_type='text/plain')

    def log_message(self, format, *args):
        # Suppress most logging to keep plugin output clean, or redirect as needed
        # print(f"[C2 Handler Log] {format % args}")
        pass


class C2ManagerPlugin(LockdoorPlugin):
    def __init__(self):
        super().__init__()
        self.agents_store: Dict[str, Dict[str, Any]] = {}
        self.listener_thread: Optional[threading.Thread] = None
        self.listener_instance: Optional[HTTPServer] = None # Typed to HTTPServer
        self.listener_status: str = "stopped" 
        self.listener_host: str = "0.0.0.0"
        self.listener_port: int = 8443
        
        self.c2_certs_dir = "./c2_certs" # Certs directory relative to project root
        self.keyfile = os.path.join(self.c2_certs_dir, "key.pem")
        self.certfile = os.path.join(self.c2_certs_dir, "cert.pem")


    def get_name(self) -> str:
        return "C2 Manager"

    def get_description(self) -> str:
        return "Manages Command and Control (C2) listeners, agents, and basic operations."

    # --- Agent Interaction Helper Methods ---
    def _generate_agent_id(self) -> str:
        return uuid.uuid4().hex

    def _register_new_agent(self, remote_ip: str, initial_data: Dict) -> str:
        agent_id = self._generate_agent_id()
        current_time = time.time()
        self.agents_store[agent_id] = {
            "agent_id": agent_id,
            "remote_ip": remote_ip,
            "initial_data": initial_data,
            "first_seen": current_time,
            "last_seen": current_time,
            "pending_commands": [], # List of command dicts: {'id': cmd_uuid, 'command': 'the command'}
            "command_history": []  # List of command dicts with status and output
        }
        return agent_id

    def _agent_beaconed(self, agent_id: str, remote_ip: str) -> bool:
        if agent_id in self.agents_store:
            self.agents_store[agent_id]['last_seen'] = time.time()
            self.agents_store[agent_id]['remote_ip'] = remote_ip # Update IP if it changed (e.g. DHCP)
            return True
        return False

    def _get_pending_command(self, agent_id: str) -> Optional[Dict[str, Any]]:
        if agent_id in self.agents_store and self.agents_store[agent_id]['pending_commands']:
            # Return the command dict {'id': cmd_uuid, 'command': 'the_command'}
            return self.agents_store[agent_id]['pending_commands'].pop(0) 
        return None

    def _store_command_output(self, agent_id: str, command_id: str, output: str) -> bool:
        if agent_id in self.agents_store:
            agent = self.agents_store[agent_id]
            for cmd_record in agent['command_history']:
                if cmd_record['id'] == command_id and cmd_record['status'] == 'sent':
                    cmd_record['output'] = output
                    cmd_record['status'] = 'executed'
                    cmd_record['completed_at'] = time.time()
                    print(f"[C2 Manager] Received output for command {command_id} from agent {agent_id}")
                    return True
            print(f"[C2 Manager] Command ID {command_id} not found or not in 'sent' state for agent {agent_id}.")
            return False
        print(f"[C2 Manager] Agent {agent_id} not found.")
        return False

    def get_actions(self) -> List[Action]:
        actions: List[Action] = [
            {
                'name': 'start_https_listener',
                'description': 'Starts the HTTPS C2 listener.',
                'parameters': [
                    ActionParameter(name='host', description='Host to bind (default: 0.0.0.0).', type='string', required=False),
                    ActionParameter(name='port', description='Port for listener (default: 8443).', type='integer', required=False)
                ]
            },
            {
                'name': 'stop_https_listener',
                'description': 'Stops the HTTPS C2 listener.',
                'parameters': []
            },
            {
                'name': 'get_listener_status',
                'description': 'Gets the current status of the C2 listener.',
                'parameters': []
            },
            {
                'name': 'list_registered_agents',
                'description': 'Lists all currently registered agents.',
                'parameters': []
            },
            {
                'name': 'get_agent_details',
                'description': 'Get details for a specific agent.',
                'parameters': [
                    ActionParameter(name='agent_id', description='The unique ID of the agent.', type='string', required=True)
                ]
            },
            {
                'name': 'send_command_to_agent',
                'description': 'Sends a command to a specific agent.',
                'parameters': [
                    ActionParameter(name='agent_id', description='The unique ID of the agent.', type='string', required=True),
                    ActionParameter(name='command', description='The command string to execute on the agent.', type='string', required=True)
                ]
            }
        ]
        return actions

    def execute_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        if action_name == 'start_https_listener':
            if self.listener_thread and self.listener_thread.is_alive():
                return {"status": "error", "message": "Listener is already running."}

            if not os.path.exists(self.keyfile) or not os.path.exists(self.certfile):
                msg = f"SSL key file ({self.keyfile}) or cert file ({self.certfile}) not found. Please generate them."
                print(f"[C2 Manager] {msg}")
                self.listener_status = "error_missing_certs"
                return {"status": "error", "message": msg}

            self.listener_host = params.get('host', self.listener_host) # Use stored default if not provided
            self.listener_port = params.get('port', self.listener_port) # Use stored default if not provided

            try:
                # Pass the plugin instance (self) to the handler factory
                def handler_factory(*args, **kwargs):
                    return SimpleC2HTTPHandler(self, *args, **kwargs)

                self.listener_instance = HTTPServer((self.listener_host, self.listener_port), handler_factory)
                
                # Wrap socket with SSL
                self.listener_instance.socket = ssl.wrap_socket(
                    self.listener_instance.socket,
                    keyfile=self.keyfile,
                    certfile=self.certfile,
                    server_side=True
                )
                
                self.listener_thread = threading.Thread(target=self.listener_instance.serve_forever, daemon=True)
                self.listener_thread.start()
                self.listener_status = "running"
                msg = f"HTTPS C2 Listener started on {self.listener_host}:{self.listener_port}"
                print(f"[C2 Manager] {msg}")
                return {"status": "success", "message": msg}
            except Exception as e:
                self.listener_status = f"error_starting: {e}"
                print(f"[C2 Manager] Error starting listener: {e}")
                return {"status": "error", "message": str(e)}
        
        elif action_name == 'stop_https_listener':
            if not self.listener_instance or not (self.listener_thread and self.listener_thread.is_alive()):
                self.listener_status = "stopped" # Ensure status is accurate
                return {"status": "info", "message": "Listener was not running."}
            
            try:
                self.listener_instance.shutdown() # Signal the server to stop
                self.listener_thread.join(timeout=5) # Wait for the thread to exit
                self.listener_status = "stopped"
                self.listener_instance = None # Clear instance
                self.listener_thread = None   # Clear thread
                msg = "HTTPS C2 Listener stopped successfully."
                print(f"[C2 Manager] {msg}")
                return {"status": "success", "message": msg}
            except Exception as e:
                self.listener_status = f"error_stopping: {e}"
                print(f"[C2 Manager] Error stopping listener: {e}")
                return {"status": "error", "message": str(e)}

        elif action_name == 'get_listener_status':
            return {
                "status": self.listener_status, 
                "host": self.listener_host, 
                "port": self.listener_port,
                "thread_active": self.listener_thread.is_alive() if self.listener_thread else False,
                "keyfile_exists": os.path.exists(self.keyfile),
                "certfile_exists": os.path.exists(self.certfile)
            }

        elif action_name == 'list_registered_agents':
            return [agent for agent_id, agent in self.agents_store.items()]


        elif action_name == 'get_agent_details':
            agent_id = params.get('agent_id')
            if not agent_id:
                return {"error": "agent_id parameter is required."}
            agent_info = self.agents_store.get(agent_id)
            if agent_info:
                return agent_info
            else:
                return {"error": f"Agent with ID '{agent_id}' not found."}

        elif action_name == 'send_command_to_agent':
            agent_id = params.get('agent_id')
            command_text = params.get('command') # Renamed to avoid conflict
            if not agent_id or not command_text:
                return {"error": "agent_id and command parameters are required."}
            
            if agent_id in self.agents_store:
                agent = self.agents_store[agent_id]
                command_id = uuid.uuid4().hex # Unique ID for this command instance
                
                command_to_queue = {'id': command_id, 'command': command_text}
                agent['pending_commands'].append(command_to_queue)
                
                # Add to command history
                agent['command_history'].append({
                    'id': command_id,
                    'command': command_text,
                    'status': 'sent', # Or 'queued' then 'sent' when beacon confirms receipt
                    'sent_at': time.time(),
                    'output': None,
                    'completed_at': None
                })
                return {"status": "success", "message": f"Command '{command_text}' (ID: {command_id}) queued for agent {agent_id}."}
            else:
                return {"error": f"Agent with ID '{agent_id}' not found."}
        else:
            return {"error": f"Action '{action_name}' not found in {self.get_name()}."}

    def load(self) -> None:
        print(f"Plugin '{self.get_name()}' loaded. Initializing C2 components.")
        # Ensure c2_certs directory exists.
        if not os.path.exists(self.c2_certs_dir):
            try:
                os.makedirs(self.c2_certs_dir)
                print(f"[C2 Manager] Created directory: {self.c2_certs_dir}")
            except OSError as e:
                print(f"[C2 Manager] Error creating directory {self.c2_certs_dir}: {e}")
        
        # Reminder for user if certs are missing
        if not os.path.exists(self.keyfile) or not os.path.exists(self.certfile):
            print(f"[C2 Manager] Reminder: SSL key/cert files ({self.keyfile}, {self.certfile}) not found.")
            print(f"[C2 Manager] Please generate them (e.g., using OpenSSL) and place them in {self.c2_certs_dir} for the HTTPS listener to work.")
            print(f"[C2 Manager] Example OpenSSL command (for testing only, use proper certs for real use):")
            print(f"[C2 Manager] openssl req -x509 -newkey rsa:2048 -keyout {self.keyfile} -out {self.certfile} -days 365 -nodes -subj \"/CN=localhost\"")


    def unload(self) -> None:
        print(f"Plugin '{self.get_name()}' unloaded. Attempting to stop listener if running.")
        if self.listener_thread and self.listener_thread.is_alive():
            print("[C2 Manager] Listener is running. Attempting to stop...")
            if self.listener_instance: # Check if instance exists
                 try:
                    self.listener_instance.shutdown() 
                    self.listener_thread.join(timeout=10) # Increased timeout slightly
                    if self.listener_thread.is_alive():
                        print("[C2 Manager] Warning: Listener thread did not terminate after shutdown and join.")
                 except Exception as e:
                    print(f"[C2 Manager] Error during listener shutdown: {e}")
            self.listener_status = "stopped"
            self.listener_instance = None
            self.listener_thread = None
            print("[C2 Manager] Listener stopped process initiated.")
        else:
            print("[C2 Manager] Listener was not running or thread already finished.")

# Make sure the plugin can be discovered.
# No other top-level executable code here.
