import os
import importlib.util
import inspect
from typing import Dict, Any, List # Added for type hinting
from .plugin_interface import LockdoorPlugin, Action # Added Action for type hinting

class PluginManager:
    def __init__(self):
        # self.plugins will store plugin instances and their actions
        # e.g., { 'plugin_name': {'instance': plugin_object, 'actions': list_of_action_dicts} }
        self.plugins: Dict[str, Dict[str, Any]] = {}

    def discover_plugins(self, plugin_folder="plugins"):
        if not os.path.exists(plugin_folder):
            print(f"Plugin folder '{plugin_folder}' not found.")
            return

        for item in os.listdir(plugin_folder):
            item_path = os.path.join(plugin_folder, item)
            if os.path.isfile(item_path) and item.endswith(".py"):
                module_name = item[:-3]
                try:
                    spec = importlib.util.spec_from_file_location(module_name, item_path)
                    if spec and spec.loader:
                        plugin_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(plugin_module)
                        self.load_plugin_from_module(plugin_module)
                    else:
                        print(f"Could not load spec for {module_name} from {item_path}")
                except Exception as e:
                    print(f"Error importing plugin module {module_name}: {e}")
            elif os.path.isdir(item_path):
                init_py_path = os.path.join(item_path, "__init__.py")
                if os.path.isfile(init_py_path):
                    module_name = item # The directory name is the module name
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, init_py_path)
                        if spec and spec.loader:
                            plugin_module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(plugin_module)
                            self.load_plugin_from_module(plugin_module)
                        else:
                            print(f"Could not load spec for {module_name} from {init_py_path}")
                    except Exception as e:
                        print(f"Error importing plugin package {module_name}: {e}")


    def load_plugin_from_module(self, plugin_module):
        for name, obj in inspect.getmembers(plugin_module):
            if inspect.isclass(obj) and issubclass(obj, LockdoorPlugin) and obj is not LockdoorPlugin:
                try:
                    plugin_instance = obj()
                    plugin_name = plugin_instance.get_name()
                    if plugin_name in self.plugins:
                        print(f"Plugin with name '{plugin_name}' already loaded. Skipping.")
                        continue
                    
                    actions: List[Action] = [] # Default to empty list
                    try:
                        actions = plugin_instance.get_actions()
                    except Exception as e:
                        print(f"Error getting actions for plugin {plugin_name}: {e}. Storing empty actions list.")
                    
                    self.plugins[plugin_name] = {
                        'instance': plugin_instance,
                        'actions': actions
                    }
                    plugin_instance.load() # Call load after storing instance and actions
                except Exception as e:
                    print(f"Error instantiating, getting actions, or loading plugin class {name} from module {plugin_module.__name__}: {e}")

    def load_plugin(self, plugin_name_or_instance: LockdoorPlugin | str):
        """
        Loads a single plugin instance or reloads if already known.
        Note: This method's utility is reduced if plugins are primarily loaded via discovery.
        It might be more relevant if plugins could be added programmatically outside the discovery process.
        """
        if isinstance(plugin_name_or_instance, LockdoorPlugin):
            plugin_instance = plugin_name_or_instance
            plugin_name = plugin_instance.get_name()
            
            if plugin_name in self.plugins:
                print(f"Plugin {plugin_name} is already loaded. Unloading first for reload.")
                self.unload_plugin(plugin_name)
            
            actions: List[Action] = []
            try:
                actions = plugin_instance.get_actions()
            except Exception as e:
                print(f"Error getting actions for plugin {plugin_name}: {e}. Storing empty actions list.")

            self.plugins[plugin_name] = {
                'instance': plugin_instance,
                'actions': actions
            }
            try:
                plugin_instance.load()
            except Exception as e:
                print(f"Error during load() method of plugin {plugin_name}: {e}")
            return True
        elif isinstance(plugin_name_or_instance, str):
            print(f"Loading plugin by name '{plugin_name_or_instance}' is not directly supported by this method. Plugins should be discovered.")
            return False
        else:
            print(f"Invalid argument for load_plugin: {plugin_name_or_instance}. Must be a plugin instance.")
            return False


    def unload_plugin(self, plugin_name: str):
        if plugin_name in self.plugins:
            plugin_data = self.plugins.pop(plugin_name)
            plugin_instance = plugin_data['instance']
            try:
                plugin_instance.unload()
            except Exception as e:
                print(f"Error during unload() method of plugin {plugin_name}: {e}")
        else:
            print(f"Plugin '{plugin_name}' not found.")

    def get_plugin(self, plugin_name: str) -> LockdoorPlugin | None:
        plugin_data = self.plugins.get(plugin_name)
        if plugin_data:
            return plugin_data['instance']
        return None

    def get_plugin_actions(self, plugin_name: str) -> List[Action] | None:
        """Returns the actions for a given plugin, or None if plugin not found."""
        plugin_data = self.plugins.get(plugin_name)
        if plugin_data:
            return plugin_data['actions']
        return None

    def list_plugins_with_details(self) -> Dict[str, Dict[str, Any]]:
        """Returns a dictionary of all plugins with their instances and actions."""
        return self.plugins
        
    def list_plugins(self) -> list[str]: # Kept for backward compatibility / simple listing
        return list(self.plugins.keys())

    def execute_plugin_action(self, plugin_name: str, action_name: str, params: Dict[str, Any]) -> Any:
        """
        Executes a specific action on a given plugin.
        """
        plugin_instance = self.get_plugin(plugin_name)
        if not plugin_instance:
            raise ValueError(f"Plugin '{plugin_name}' not found.")
        
        # Validate if the action_name is one of the plugin's declared actions (optional but good practice)
        # plugin_actions = self.get_plugin_actions(plugin_name)
        # if not any(action['name'] == action_name for action in (plugin_actions or [])):
        #     raise ValueError(f"Action '{action_name}' not found or not declared by plugin '{plugin_name}'.")

        try:
            return plugin_instance.execute_action(action_name, params)
        except Exception as e:
            print(f"Error executing action '{action_name}' for plugin '{plugin_name}': {e}")
            # Depending on desired error handling, could re-raise or return an error object
            raise # Re-raise the exception to make the caller aware


# Example Usage (Optional - for testing, can be removed or put in a test file)
if __name__ == '__main__':
    # This example assumes you have a 'plugins' directory at the project root
    # and a sample plugin implementing the new interface.
    
    # project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # plugins_dir = os.path.join(project_root, "plugins")

    # print(f"Looking for plugins in: {plugins_dir}")
    
    manager = PluginManager()
    # manager.discover_plugins(plugins_dir) # Adjust path if needed

    # print("\nLoaded plugins with details:")
    # for name, details in manager.list_plugins_with_details().items():
    #    print(f"  Plugin: {name}")
    #    print(f"    Instance: {details['instance']}")
    #    print(f"    Actions: {details['actions']}")

    # Example: if you had an 'about_plugin' that declared an action 'get_info'
    # if "About Lockdoor" in manager.list_plugins():
    #     try:
    #         print("\nExecuting 'get_info' from 'About Lockdoor':")
    #         result = manager.execute_plugin_action("About Lockdoor", "get_info", {})
    #         print(f"Result: {result}")
    #     except Exception as e:
    #         print(f"Could not execute action: {e}")
    pass
