<p align="center">
  <img src="https://avatars.githubusercontent.com/u/55242164?s=400">
</p>

<h2 align="center"> Lockdoor - Python Plugin Framework<br>
</h2>

**Note:** This project has been significantly refactored from its original Bash-based version into a Python-based plugin framework with a web interface. The original tools and functionalities are intended to be progressively integrated as plugins into this new architecture. The information below is being updated to reflect these changes.

# Table of contents

- [Table of contents](#table-of-contents)
- [Overview 📙 :](#overview--)
- [Features (New Framework) 📙 :](#features-new-framework--)
- [Installation 🛠️ :](#installation-%EF%B8%8F-)
- [Plugin Development](#plugin-development)
- [Multi-platform Support 🌍](#multi-platform-support-)
- [C2 Module (MVP)](#c2-module-mvp)
- [Changelog (Historical) 📌 :](#changelog-historical--)
- [Badges 📌 :](#badges--)
- [Support me (Original Author) 💰 :](#support-me-original-author--)
- [Contributors (Original Project) ⭐ :](#contributors-original-project--)
- [Versions (Historical)](#versions-historical)
- [Blogs & Articles (Historical) 📰 :](#blogs--articles-historical--)
- [Screenshots & Demos (Historical) 💻 :](#screenshots--demos-historical--)
- [Lockdoor Tools contents (Legacy - To be Integrated) 🛠️ :](#lockdoor-tools-contents-legacy---to-be-integrated-%EF%B8%8F-)
- [Lockdoor Resources contents (Legacy - To be Integrated) 📚 :](#lockdoor-resources-contents-legacy---to-be-integrated--)
- [**Contributing** :](#contributing-)

# Overview 📙 :

*LockDoor* was originally a Framework aimed at **helping penetration testers, bug bounty hunters And cyber security engineers**.
This tool was designed for Debian/Ubuntu/ArchLinux based distributions to create a similar and familiar distribution for Penetration Testing, containing favorite and most used tools by Pentesters.
As pentesters, most of us has his personal ' /pentest/ ' directory so this Framework was helping you to build a perfect one.

The new version of Lockdoor is a **Python-based plugin framework** that aims to provide a modular and extensible platform for cybersecurity tools, managed via a web-based interface.

# Features (New Framework) 📙 :

-   **Plugin-Based Architecture:** Easily extend functionality by adding new plugins.
-   **Web Panel:** Manage and interact with plugins through a web interface (powered by Flask).
-   **Dynamic Plugin Discovery:** Plugins placed in the `plugins/` directory are automatically loaded.
-   **Dockerized Deployment:** Simplified setup and deployment using Docker.
-   **Core Plugin Management:** Centralized system for loading, unloading, and accessing plugins.
-   **Extensible Interface:** Define custom functionalities within your plugins.

*(Note: The original features listed below are from the legacy version and will be re-evaluated for integration into the new plugin system.)*
  - **Pentesting Tools Selection 📙 :** (Legacy) Tools were a collection from Kali, Parrot OS, BlackArch, and GitHub.
  - **Resources and cheatsheets 📙 :** (Legacy) Included report templates, walkthroughs, and cheatsheets.

# Installation 🛠️ :

This framework is designed to be run using Docker.

**Prerequisites:**
- Docker installed on your system.

**Building and Running the Framework:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/SofianeHamlaoui/Lockdoor-Framework.git # Or your fork's URL
    cd Lockdoor-Framework
    ```

2.  **Build the Docker image:**
    From the root of the repository (where `docker/Dockerfile` is located):
    ```bash
    docker build -t lockdoor-plugin-framework -f docker/Dockerfile .
    ```

3.  **Run the Docker container:**
    ```bash
    docker run -d -p 5000:5000 --name lockdoor-app lockdoor-plugin-framework
    ```
    - `-d` runs the container in detached mode.
    - `-p 5000:5000` maps port 5000 on your host to port 5000 in the container (where Flask runs).
    - You can access the web panel by navigating to `http://localhost:5000` in your browser.

**Accessing Logs:**
```bash
docker logs lockdoor-app
```

**Stopping and Removing the Container:**
```bash
docker stop lockdoor-app
docker rm lockdoor-app
```

# Plugin Development

The Lockdoor Framework now supports a plugin-based architecture. Plugins are Python modules that extend the framework's functionality.

**1. Plugin Structure:**
   - Plugins are Python files (`.py`) placed in the `plugins/` directory at the root of the project.
   - Each plugin file must contain a class that inherits from `LockdoorPlugin` (defined in `src.plugin_framework_core.plugin_interface`).

**2. Implementing the `LockdoorPlugin` Interface:**
   Your plugin class must implement the following methods from the `LockdoorPlugin` base class:

   - **`get_name(self) -> str`**:
     Return the display name of the plugin.
     ```python
     def get_name(self) -> str:
         return "My Awesome Plugin"
     ```

   - **`get_description(self) -> str`**:
     Return a short description of what the plugin does.
     ```python
     def get_description(self) -> str:
         return "This plugin performs awesome task X and Y."
     ```

   The following methods are optional and can be overridden:
   - **`load(self) -> None`**: Code to run when the plugin is loaded.
   - **`unload(self) -> None`**: Code to run when the plugin is unloaded.

   **Defining Actions:**
   Plugins can expose specific functionalities as "actions". These actions are discoverable by the framework and can be invoked.

   - **`get_actions(self) -> List[Action]`**:
     Return a list of actions your plugin provides. Each action is defined as a dictionary (conforming to the `Action` TypedDict structure from `plugin_interface.py`).
     ```python
     from src.plugin_framework_core.plugin_interface import Action, ActionParameter # If you want to be explicit with types
     from typing import List, Dict, Any # For execute_action

     # ... inside your plugin class ...
     def get_actions(self) -> List[Action]: # Or List[Dict[str, Any]]
         return [
             {
                 'name': 'my_action_1',
                 'description': 'Performs the first awesome thing.',
                 'parameters': [
                     {'name': 'input_data', 'description': 'Data to process', 'type': 'string', 'required': True},
                     {'name': 'threshold', 'description': 'A threshold value', 'type': 'integer', 'required': False}
                 ]
             },
             {
                 'name': 'my_simple_action',
                 'description': 'Does something simple without parameters.',
                 'parameters': []
             }
         ]
     ```
     Each parameter in the `parameters` list is also a dictionary (conforming to `ActionParameter`), specifying its `name`, `description`, `type` (e.g., 'string', 'integer', 'boolean', 'file'), and whether it's `required`.

   - **`execute_action(self, action_name: str, params: Dict[str, Any]) -> Any`**:
     This method is called by the framework to run a specific action.
     ```python
     # ... inside your plugin class ...
     def execute_action(self, action_name: str, params: Dict[str, Any]) -> Any:
         if action_name == 'my_action_1':
             data = params.get('input_data')
             threshold = params.get('threshold', 0) # Default value if not provided
             if data is None: # Or based on 'required': True
                 return {"error": "Missing required parameter: input_data"}
             # ... perform the action ...
             return f"Processed '{data}' with threshold {threshold}."
         elif action_name == 'my_simple_action':
             # ... perform the simple action ...
             return "Simple action executed successfully."
         else:
             # It's good practice to handle unknown actions, though the framework might also check.
             return {"error": f"Action '{action_name}' not found."}
     ```
     The `params` dictionary contains the parameters passed by the caller. The method can return any type of result (string, dictionary, list, etc.), which should ideally be serializable if it's to be displayed in the web UI.

**3. Discovery:**
   - The framework will automatically discover any valid plugin files in the `plugins/` directory when it starts.
   - Discovered plugins and their actions (including parameter details) will be listed in the web panel under the "/plugins" route.

**4. Example:**
   See `plugins/about_plugin.py` and `plugins/utilities_plugin.py` for examples. (Note: `about_plugin.py` has been updated to use the new action system).

## Multi-platform Support 🌍

The Lockdoor Plugin Framework is designed with multi-platform support in mind, targeting **Windows, Linux, and macOS**.

**Key Approaches:**

*   **Docker for Deployment:** The primary method for running the framework is via Docker. Docker containers encapsulate all dependencies and provide a consistent environment across different operating systems. This means that if you can run Docker on your system, you can run the Lockdoor Framework.
*   **Python Core:** The core framework and web panel are written in Python, a cross-platform language.
*   **Platform-Agnostic Plugins (Goal):**
    *   Plugin developers are encouraged to write their Python code to be platform-agnostic whenever possible.
    *   Standard Python libraries and well-established third-party packages generally offer good cross-platform compatibility.
    *   If a plugin *must* interact with platform-specific tools or APIs (e.g., calling a command-line tool that is only available on Linux), this should be clearly documented within the plugin's description or its own documentation. The framework itself does not restrict this, but users should be aware of such dependencies when using specific plugins.

**Considerations for Plugin Developers:**

*   Avoid hardcoding paths; use `os.path.join()` and other `os` module features for path manipulation.
*   Be mindful of differences in shell commands or system utilities if your plugin uses `subprocess` to call external tools. Consider checking the OS (e.g., using `platform.system()`) and adapting behavior if necessary.
*   If your plugin requires external non-Python dependencies, these would ideally be installable within the Docker environment. If they are host-system dependencies, this makes the plugin less portable.

# C2 Module (MVP)

A basic Command and Control (C2) module has been added as a plugin named "C2 Manager". This provides foundational capabilities for remote agent interaction.

**Features (MVP):**
-   HTTPS Listener for encrypted communications.
-   Agent Registration: New agents can register with the C2.
-   Agent Beaconing: Registered agents periodically check in.
-   Basic Command Tasking: Send commands to agents and receive their output.
-   Web Panel Integration: Manage the listener and interact with agents through the Flask web interface.

**SSL Certificate Requirement:**
The HTTPS C2 listener requires SSL certificates (`key.pem` and `cert.pem`) to function.
1.  Create a directory named `c2_certs` in the root of the Lockdoor Framework project (i.e., alongside `run.py` and `plugins/`).
2.  Place your `key.pem` and `cert.pem` files into this `./c2_certs/` directory.

For testing purposes, you can generate self-signed certificates. The C2 Manager plugin will print a reminder and an example OpenSSL command to your console when it loads if these files are missing. Here's an example command:
```bash
# First, ensure the ./c2_certs directory exists:
mkdir -p ./c2_certs

# Then, generate the self-signed certificates:
openssl req -x509 -newkey rsa:2048 -keyout ./c2_certs/key.pem -out ./c2_certs/cert.pem -days 365 -nodes -subj "/CN=localhost"
```
**Note:** For any real-world use, replace self-signed certificates with properly issued ones.

**Managing the C2 Listener (Web Panel):**
1.  Start the Lockdoor Framework: `docker run ...` (as per Installation instructions).
2.  Access the web panel (usually `http://localhost:5000`).
3.  Navigate to "C2 Management" from the main navigation (this link will appear once the C2 blueprint is integrated). Then select the "Listeners" tab.
4.  The page displays the current listener status (e.g., "stopped", "running", "error_missing_certs").
5.  If certificates are in place, you can set the desired host and port (defaults to `0.0.0.0` and `8443`) and click "Start Listener".
6.  To stop the listener, click "Stop Listener".

**Running the Test Agent:**
A basic Python C2 agent is provided in `dev_tools/c2_agent/basic_agent.py` for testing the C2 functionality.
1.  **Ensure the C2 Listener is Started:** Use the web panel as described above to start the HTTPS listener.
2.  **Configure the Agent:**
    *   Open `dev_tools/c2_agent/basic_agent.py`.
    *   Verify `C2_URL`: It defaults to `https://localhost:8443`. Adjust if your Docker container is mapped to a different host or port externally.
    *   If using the self-signed certificate generated above, ensure `VERIFY_SSL = False` in the agent script. For valid certs, set this to `True` or the path to your CA bundle.
3.  **Run the Agent:**
    Execute the agent script from your terminal (from the project root directory):
    ```bash
    python dev_tools/c2_agent/basic_agent.py
    ```
    The agent will attempt to register with the C2 listener and then start beaconing.

**Interacting with Agents (Web Panel):**
1.  Navigate to "C2 Management" -> "Agents" in the web panel.
2.  Once the test agent (or any other compatible agent) registers, it will appear in the list.
3.  Click on an "Agent ID" (or a "Details" button) to go to the agent detail page.
4.  On the agent detail page, you can:
    *   View more information about the agent (IP, registration data, last seen).
    *   Enter commands in the "Send Command" form and submit them.
    *   View the history of commands sent to the agent and their outputs.

# Changelog (Historical) 📌 :
  #### Version v2.3 IS OUT !! (Original Project)

        - Fixing some CI 
        - making a more stable version 
        - new docker iaage build
        - adding packages for each supported distros

# Badges 📌 :
*(Badges below refer to the original project state)*
![made-with-python]( http://ForTheBadge.com/images/badges/made-with-python.svg)
![GitHub](https://badgen.net/github/release/SofianeHamlaoui/Lockdoor-Framework)
![License](https://badgen.net/pypi/license/lockdoor)
![TestedON](https://img.shields.io/badge/Tested%20on%20%20-Linux%20%26%20Windows-blue)


# Support me (Original Author) 💰 :
   *(The following support information refers to the original author of the Lockdoor project)*
   - BTC Addresse : 1NR2oqsuevvWJwzCyhBXmqEA5eYAaSoJFk

# Contributors (Original Project) ⭐ :
*(Contributors listed below are for the original Lockdoor project)*
![commits](https://badges.pufler.dev/contributors/SofianeHamlaoui/Lockdoor-Framework)

# Versions (Historical)
*(The versions below refer to the original Bash-based Lockdoor project. The new Python framework starts at v0.1.0 as per `pyproject.toml`)*

#### 06/2021 : 2.3

- Config file checking.
- Updating the tools.
- Showing the current version of Lockdoor by -v arg.
- checking the version and asking for possible update.
- Making it easier to customize.
- No added tools for the moment.
- Fixing the docker misconfiguration, the docker version now works perfectly.

    - Information Gathring Tools (21)
    - Web Hacking Tools(15)
    - Reverse Engineering Tools (15)
    - Exploitation Tools (6)
    - Pentesting & Security Assessment Findings Report Templates (6)
    - Password Attack Tools (4)
    - Shell Tools + Blackarch's Webshells Collection (4)
    - Walk Throughs & Pentest Processing Helpers (3)
    - Encryption/Decryption Tools (2)
    - Social Engineering tools (1)
    - All you need as Privilege Escalation scripts and exploits

#### 03/2020 : 2.2.3
   - Information Gathring Tools (21)
   - Web Hacking Tools(15)
   - Reverse Engineering Tools (15)
   - Exploitation Tools (6)
   - Pentesting & Security Assessment Findings Report Templates (6)
   - Password Attack Tools (4)
   - Shell Tools + Blackarch's Webshells Collection (4)
   - Walk Throughs & Pentest Processing Helpers (3)
   - Encryption/Decryption Tools (2)
   - Social Engineering tools (1)
   - All you need as Privilege Escalation scripts and exploits
   - Working on Kali,Ubuntu,Arch,Fedora,Opensuse and Windows (Cygwin)

# Blogs & Articles (Historical) 📰 :
*(The following blogs and articles refer to the original Lockdoor project)*
      * Reddit : https://www.reddit.com/r/cybersecurity/comments/d4hthh/lockdoor_a_penetration_testing_framework_with/
      * Medium.com : https://medium.com/@SofianeHamlaoui/lockdoor-framework-a-penetration-testing-framework-with-cyber-security-resources-sofiane-22fbb7942378
      * Xploit Lab : https://xploitlab.com/lockdoor-framework-penetration-testing-framework-with-cyber-security-resources/
      * Station X : https://www.stationx.net/threat-intelligence-17th-september/
      * Kelvin Security : https://blog.kelvinsecurity.com/2019/09/12/lookdoor-framework-a-penetration-testing-framework-with-cyber-security-resources/
      * All About hacking : https://www.allabouthack.com/2019/09/lookdoor-framework-penetration-testing.html
      * Wired Intel : http://wiredintel.bravehost.com/wired/2019/09/15/%F0%9F%94%90-lockdoor-a-penetration-testing-framework-with-cyber-security-resources

            * Social networks :
                  * LinkedIn :
                        * By Nermin S. : https://www.linkedin.com/posts/nsmajic_sofianehamlaouilockdoor-framework-activity-6578952540564529152-B-0P
                  * Twitter :
                        * By Me :D : https://twitter.com/S0fianeHamlaoui/status/1173079963567820801
                        * National Cyber Security Services : https://twitter.com/NationalCyberS1/status/1173917454151475202
                        * Xploit Lab : https://twitter.com/xploit_lab/status/1173990273644261376
                        * More : https://twitter.com/search?q=Lockdoor%20Framework
                        * More : https://twitter.com/search?q=Lookdoor%20Framework
                  * Facebook :
                        * By ME :D : https://www.facebook.com/S0fianeHamlaoui/posts/678704759315090
                        * National Cyber Security Services : https://www.facebook.com/ncybersec/posts/1273735519463836
                        * Xploit Lab : https://www.facebook.com/XploitLab/posts/2098443780463126
                        * Root Developers : https://www.facebook.com/root.deve/posts/1181412315364265
                        * More : https://www.facebook.com/search/top/?q=Lockdoor%20Framework
            * Youtube :
                  * My youtube video : https://www.youtube.com/watch?v=_agvb29FQrs
                  * The Shadow Brokers video : https://www.youtube.com/watch?v=6njKRrKQtow

# Screenshots & Demos (Historical) 💻 :

**Note:** The screenshots and demos below are from the **original Bash-based version** of Lockdoor and **do not reflect the new Python-based plugin framework and web panel.** They will be updated in the future.

| ![](https://sofianehamlaoui.github.io/junk/lockdoor/screenshots/installation-dir-1.png) | ![](https://sofianehamlaoui.github.io/junk/lockdoor/screenshots/verbosemode.png) | ![](https://sofianehamlaoui.github.io/junk/lockdoor/screenshots/RootMenu.png) | ![](https://sofianehamlaoui.github.io/junk/lockdoor/screenshots/infogath.png) | ![](https://sofianehamlaoui.github.io/junk/lockdoor/screenshots/webhack.png) | ![](https://sofianehamlaoui.github.io/junk/lockdoor/screenshots/exploitation.png) | ![](https://sofianehamlaoui.github.io/junk/lockdoor/screenshots/about.png) |
|-----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------------------------------|

| ![](https://sofianehamlaoui.github.io/junk/lockdoor/gifs/kali.gif) | ![](https://sofianehamlaoui.github.io/junk/lockdoor/gifs/ubuntu.gif) | ![](https://sofianehamlaoui.github.io/junk/lockdoor/gifs/archlinux.gif) | ![](https://sofianehamlaoui.github.io/junk/lockdoor/gifs/fedora.gif) | ![](https://sofianehamlaoui.github.io/junk/lockdoor/gifs/opensuse.gif) | ![](https://sofianehamlaoui.github.io/junk/lockdoor/gifs/windows.gif) |
|-|-|-|-|-|-|

# Lockdoor Tools contents (Legacy - To be Integrated) 🛠️ :

**Note:** The following list of tools is from the original Lockdoor project. These are planned to be refactored or integrated as plugins into the new framework. Their availability in the new system is not yet guaranteed.

## **Information Gathering** :mag_right: :
   - Tools: dirsearch, brut3k1t, gobuster, etc.
   - Frameworks: ReconDog, RED_HAWK, Dracnmap

## **Web Hacking** 🌐 :
   - Tools: Spaghetti, CMSmap, BruteXSS, etc.
   - Frameworks: Dzjecter

## **Privilege Escalation** ⚠️ :
   - Tools: Linux scripts, Windows checks, MySQL UDFs

## **Reverse Engineering** ⚡:
   - Tools: Radare2, VirtusTotal, Miasm, etc.

## **Exploitation** ❗:
   - Tools: Findsploit, Pompem, rfix, etc.

## **Shells** 🐚:
   - Tools: WebShells, ShellSum, Weevely, etc.

## **Password Attacks** ✳️:
   - Tools: crunch, CeWL, patator

## **Encryption - Decryption** 🛡️:
   - Tools: Codetective, findmyhash

## **Social Engineering** 🎭:
   - Tools: scythe

# Lockdoor Resources contents (Legacy - To be Integrated) 📚 :

**Note:** The resources listed below are from the original Lockdoor project. The `ToolsResources` directory still exists in the repository, but these materials are not yet directly integrated into the new plugin framework's web interface. Their future integration will be assessed.

## **Information Gathering** :mag_right: :
> - [Cheatsheet\_SMBEnumeration](ToolsResources/INFO-GATH/CHEATSHEETS/Cheatsheet_SMBEnumeration.txt)
> - ... (other cheatsheets)

## **Crypto** 🛡️:
> -   [Crypto101.pdf](ToolsResources/ENCRYPTION/CHEATSHEETS/Crypto101.pdf)

## **Exploitation** ❗:
> -   [computer\_network\_exploits](ToolsResources/EXPLOITATION/CHEATSHEETS/computer_network_exploits.md)
> - ... (other cheatsheets)

## **Networking** 🖧 :
> -   [bpf\_syntax](ToolsResources/NETWORKING/bpf_syntax.md)
> - ... (other cheatsheets)

*(Other resource categories from the original README.md would follow a similar pattern: kept for now, but marked as legacy and for future integration review)*

# **Contributing** :

   0. Read [Contributing](https://github.com/SofianeHamlaoui/Lockdoor-Framework/blob/master/docs/CONTRIBUTING.md), [The Code of Conduct](https://github.com/SofianeHamlaoui/Lockdoor-Framework/blob/master/docs/CODE_OF_CONDUCT.md) and [The pull request template](https://github.com/SofianeHamlaoui/Lockdoor-Framework/blob/master/docs/pull_request_template.md)
      *(Note: These contribution guidelines may need to be updated to reflect the new Python project structure and development workflow.)*
   1. Fork it (https://github.com/SofianeHamlaoui/Lockdoor-Framework/fork)
   2. Create your feature branch
   3. Commit your changes
   4. Push to the branch
   5. Create a new Pull Request
