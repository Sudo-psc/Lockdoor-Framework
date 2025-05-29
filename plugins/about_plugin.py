from src.plugin_framework_core.plugin_interface import LockdoorPlugin

class AboutPlugin(LockdoorPlugin):
    def get_name(self) -> str:
        return "About Lockdoor"

    def get_description(self) -> str:
        return "Displays information about the Lockdoor Framework."

    def load(self) -> None:
        # print(f"Plugin '{self.get_name()}' loaded.") # Optional: for CLI debugging
        pass

    def unload(self) -> None:
        # print(f"Plugin '{self.get_name()}' unloaded.") # Optional: for CLI debugging
        pass

    def get_about_info(self) -> str:
        # Adapted from the original lockdoors/about.py show() function
        # The shrts.clscprilo(), shrts.oktocont(), and main.menu() calls are omitted
        # as they are CLI-specific and not suitable for a general info-returning method.
        # The color codes are also removed for broader compatibility (e.g., HTML display).
        
        # The ASCII art from the example will be used as the original `clscprilo()` is not available
        # and its output is unknown. A more generic header is used.
        
        about_text = """
#############################################################
#                   Lockdoor Framework                      #
#  A Penetration Testing framework with CyberSec Resources  #
#############################################################
#    -- Version: v2.2.4 15/08/2020 (Original Version)       #
#    -- Developer: Sofiane Hamlaoui                         #
#    -- Thanks: No One                                      #
#############################################################

                        -[!]-Description-[!]-
LockDoor is a Framework aimed at helping penetration testers,
bug bounty hunters And cyber security engineers.
This tool is designed for Debian/Ubuntu/ArchLinux based
distributions to create a similar and familiar distribution
for Penetration Testing. But containing the favorite and the most used tools by
Pentesters.
As pentesters, most of us has his personal ' /pentest/ ' directory so this
Framework is helping you to build a perfect one.

---
Note: This information is from the original Lockdoor framework.
The plugin system is a new addition.
"""
        return about_text

# Example of how to potentially use this plugin's output (for testing/dev):
# if __name__ == '__main__':
#     plugin = AboutPlugin()
#     print(f"Plugin Name: {plugin.get_name()}")
#     print(f"Plugin Description: {plugin.get_description()}")
#     plugin.load()
#     print("\n--- About Info ---")
#     print(plugin.get_about_info())
#     plugin.unload()
