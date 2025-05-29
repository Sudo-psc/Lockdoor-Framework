from src.plugin_framework_core.plugin_interface import LockdoorPlugin, Action, ActionParameter
from typing import List, Dict, Any

class UtilitiesPlugin(LockdoorPlugin):
    # Adapted from the original printlogo() in lockdoors/shrts.py
    # Color codes are removed for better compatibility with various UIs (e.g., web)
    # The original logo had multiple color codes; this version is plain text.
    _LOGO = """
            ..',,,'..           
         .',;;;;;;;;,'.         
      ..,;;;;;;;;;;;;;;,..      
     .,;;;,'..'''''.',;;;,.     
     .;;;;.  ..   .. .;;;;'      (                                         
     .,;;;.  ...     .;;;;.      ) )               )  (                   
      ..,;,.  ...   .,;,..       (()/(            ( /(  )\ )           (   
        .';;'.    .',;'.         /(_))  (    (   )\())(()/(  (    (   )(   
    ..',,;;;;;,,,,;;;;;,,'..     (_))    )\   )\ ((_)\  ((_)) )\   )\ (()\ 
  .','.....................''.   | |    ((_) ((_)| |(_) _| | ((_) ((_) ((_)\ 
 .',..',,,,,,,,,,,,,,,,,,,..,,.  | |__ / _ \/ _| | / // _` |/ _ \/ _ \| '_| 
 .;,..,;;;;;;'....';;;;;;;..,;.  |____|\___/\__| |_\_\\__,_|\___/\___/|_|  
 ';;..,;;;;;,..,,..';;;;;,..,;'            © Sofiane Hamlaoui | 2024       
.';;..,;;;;,. .... .,;;;;,..;;,. Lockdoor : A Penetration Testing framework
 ';;..,;;;;'  ....  .;;;;,..;;,.                  v2.3 (Original)
 .,;'.';;;;'.  ..  .';;;;,.';,.  
   ....;;;;;,'''''',;;;;;'...    
       ..................
    """

    _SEPARATOR = "\n-------------------------------------------------------------------------------------------------------------------\n"

    def get_name(self) -> str:
        return "Utilities"

    def get_description(self) -> str:
        return "Provides common utility functions and text snippets, adapted from the original shrts.py."

    def load(self) -> None:
        pass # No specific load actions needed for this utility plugin

    def unload(self) -> None:
        pass # No specific unload actions needed

    def get_actions(self) -> List[Action]:
        actions: List[Action] = [
            {
                'name': 'get_logo',
                'description': 'Returns the Lockdoor ASCII art logo (adapted from original).',
                'parameters': []
            },
            {
                'name': 'format_message',
                'description': 'Formats a message string with a standard prefix (info, error, success, warning, event).',
                'parameters': [
                    ActionParameter(name='text', description='The message text.', type='string', required=True),
                    ActionParameter(name='type', description='Message type (info, error, success, warning, event). Default: info.', type='string', required=False)
                ]
            },
            {
                'name': 'get_separator_line',
                'description': 'Returns a standard separator line string.',
                'parameters': []
            }
        ]
        return actions

    def execute_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        if action_name == 'get_logo':
            return self._LOGO
        elif action_name == 'format_message':
            text = params.get('text')
            msg_type = params.get('type', 'info').lower() # Default to info

            if text is None: # Check for None explicitly, as empty string might be valid for some
                return "[!] ERROR: 'text' parameter is missing for format_message action."

            prefix = "[*]" # Default prefix for unknown types
            if msg_type == 'info':
                prefix = "[+]"
            elif msg_type == 'error':
                prefix = "[!]"
            elif msg_type == 'success':
                prefix = "[>]"
            elif msg_type == 'warning':
                prefix = "[?]"
            elif msg_type == 'event':
                prefix = "[#]"
            
            # Ensure msg_type is capitalized for the output string as per example
            return f"{prefix} {msg_type.upper()}: {text}"
            
        elif action_name == 'get_separator_line':
            return self._SEPARATOR
        else:
            # It's good practice to raise an error for unknown actions
            # or return a specific error message structure if preferred by the framework.
            raise ValueError(f"Action '{action_name}' not found in {self.get_name()}.")

# Example Usage (for direct testing of this file, not part of the framework execution)
if __name__ == '__main__':
    plugin = UtilitiesPlugin()
    print(f"Plugin Name: {plugin.get_name()}")
    print(f"Plugin Description: {plugin.get_description()}")
    
    print("\nAvailable Actions:")
    for action_def in plugin.get_actions():
        print(f"  - {action_def['name']}: {action_def['description']}")
        if action_def['parameters']:
            print("    Parameters:")
            for param in action_def['parameters']:
                print(f"      - {param['name']} ({param.get('type', 'any')})")

    print("\n--- Testing get_logo ---")
    logo_output = plugin.execute_action('get_logo', {})
    print(logo_output)

    print("\n--- Testing format_message ---")
    msg1 = plugin.execute_action('format_message', {'text': 'This is an info message.'})
    print(msg1)
    msg2 = plugin.execute_action('format_message', {'text': 'Critical failure!', 'type': 'error'})
    print(msg2)
    msg3 = plugin.execute_action('format_message', {'text': 'Operation completed.', 'type': 'success'})
    print(msg3)
    msg4 = plugin.execute_action('format_message', {'text': 'Something looks odd.', 'type': 'warning'})
    print(msg4)
    msg5 = plugin.execute_action('format_message', {'text': 'User logged in.', 'type': 'event'})
    print(msg5)
    msg_missing_text = plugin.execute_action('format_message', {'type': 'info'}) # Test missing text
    print(msg_missing_text)


    print("\n--- Testing get_separator_line ---")
    sep_output = plugin.execute_action('get_separator_line', {})
    print(sep_output)

    print("\n--- Testing unknown action ---")
    try:
        unknown_output = plugin.execute_action('do_something_else', {})
        print(unknown_output)
    except ValueError as e:
        print(f"Caught expected error: {e}")

```
