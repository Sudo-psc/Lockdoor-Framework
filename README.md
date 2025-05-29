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
   Your plugin class must implement the following methods:

   ```python
   from src.plugin_framework_core.plugin_interface import LockdoorPlugin

   class MyCustomPlugin(LockdoorPlugin):
       def get_name(self) -> str:
           return "My Custom Plugin"

       def get_description(self) -> str:
           return "This is a brief description of what my plugin does."

       def load(self) -> None:
           # Optional: Code to run when the plugin is loaded
           print(f"Plugin '{self.get_name()}' loaded successfully.")

       def unload(self) -> None:
           # Optional: Code to run when the plugin is unloaded
           print(f"Plugin '{self.get_name()}' unloaded.")

       # You can add custom methods for your plugin's logic
       def my_custom_action(self, data: str) -> str:
           return f"Processed: {data.upper()}"
   ```

**3. Discovery:**
   - The framework will automatically discover any valid plugin files in the `plugins/` directory when it starts.
   - Discovered plugins will be listed in the web panel under the "/plugins" route.

**4. Example:**
   See `plugins/about_plugin.py` for a simple example of a plugin.

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
