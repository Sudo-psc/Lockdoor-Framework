from src.plugin_framework_core.plugin_interface import LockdoorPlugin, Action
from typing import List, Dict, Any

class AboutPlugin(LockdoorPlugin):
    def get_name(self) -> str:
        return "About Lockdoor"

    def get_description(self) -> str:
        return "Displays information about the Lockdoor Framework."

    def load(self) -> None:
        pass

    def unload(self) -> None:
        pass

    def _get_info_content(self) -> str: # Renamed from get_about_info
        # Adapted from the original lockdoors/about.py show() function
        # The shrts.clscprilo(), shrts.oktocont(), and main.menu() calls are omitted
        # as they are CLI-specific and not suitable for a general info-returning method.
        # The color codes are also removed for broader compatibility (e.g., HTML display).
        
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

    def get_actions(self) -> List[Action]:
        actions: List[Action] = [
            {
                'name': 'get_info',
                'description': 'Returns detailed information about the Lockdoor framework (original version).',
                'parameters': [] # No parameters for this action
            }
        ]
        return actions

    def execute_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        if action_name == 'get_info':
            return self._get_info_content()
        else:
            # It's good practice to raise an error or return an error structure
            # if the action is not recognized.
            return {"error": f"Action '{action_name}' not found in {self.get_name()}."}

# Example of how to potentially use this plugin's output (for testing/dev):
# if __name__ == '__main__':
#     plugin = AboutPlugin()
#     print(f"Plugin Name: {plugin.get_name()}")
#     print(f"Plugin Description: {plugin.get_description()}")
#     plugin.load()
    
#     actions = plugin.get_actions()
#     print("\nAvailable Actions:")
#     for act_def in actions:
#         print(f"  - {act_def['name']}: {act_def['description']}")

#     if actions:
#         action_to_test = actions[0]['name']
#         print(f"\n--- Testing Action: {action_to_test} ---")
#         result = plugin.execute_action(action_to_test, {})
#         print(result)
    
#     plugin.unload()
