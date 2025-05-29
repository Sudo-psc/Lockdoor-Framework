import os
import importlib.util
import inspect
from .plugin_interface import LockdoorPlugin

class PluginManager:
    def __init__(self):
        self.plugins = {}

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
                # Handle subdirectories (potential plugin packages)
                # For now, we'll assume plugins are single .py files or a specific structure
                # e.g. a __init__.py that registers the plugin or contains the plugin class
                init_py_path = os.path.join(item_path, "__init__.py")
                if os.path.isfile(init_py_path):
                    module_name = item # The directory name is the module name
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, init_py_path)
                        if spec and spec.loader:
                            plugin_module = importlib.util.module_from_spec(spec)
                            # Add the parent of plugin_folder to sys.path to allow relative imports
                            # within the plugin package if the plugin is a directory.
                            # This is a simplified approach. For robust package handling,
                            # consider installing plugins or using more sophisticated path management.
                            # parent_dir = os.path.dirname(plugin_folder)
                            # if parent_dir not in sys.path:
                            #    sys.path.insert(0, parent_dir)
                            spec.loader.exec_module(plugin_module)
                            # if parent_dir in sys.path and parent_dir != ".":
                            #    sys.path.pop(0)
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
                    self.plugins[plugin_name] = plugin_instance
                    plugin_instance.load()
                except Exception as e:
                    print(f"Error instantiating or loading plugin class {name} from module {plugin_module.__name__}: {e}")

    def load_plugin(self, plugin_name_or_instance):
        """
        Loads a single plugin instance or reloads if already known.
        This is a simplified version; actual loading might involve more complex path resolution
        or direct module loading if the plugin isn't discovered through the folder scan.
        """
        if isinstance(plugin_name_or_instance, LockdoorPlugin):
            plugin_instance = plugin_name_or_instance
            plugin_name = plugin_instance.get_name()
            if plugin_name in self.plugins:
                print(f"Plugin {plugin_name} is already loaded. Unloading first for reload.")
                self.unload_plugin(plugin_name)
            
            self.plugins[plugin_name] = plugin_instance
            try:
                plugin_instance.load()
            except Exception as e:
                print(f"Error during load() method of plugin {plugin_name}: {e}")
            return True
        elif isinstance(plugin_name_or_instance, str):
            # This part assumes the plugin was already discovered and is in self.plugins
            # but somehow marked as unloaded (not implemented here) or needs reloading.
            # For dynamic loading of a specific file not in the folder, a different mechanism would be needed.
            print(f"Loading plugin by name '{plugin_name_or_instance}' is not fully supported in this basic version without prior discovery.")
            # Example: if you had a way to get the module/class by name:
            # plugin_instance = self._get_plugin_instance_by_name(plugin_name_or_instance)
            # if plugin_instance:
            #    return self.load_plugin(plugin_instance)
            return False
        else:
            print(f"Invalid argument for load_plugin: {plugin_name_or_instance}. Must be a plugin name (str) or instance.")
            return False


    def unload_plugin(self, plugin_name: str):
        if plugin_name in self.plugins:
            plugin_instance = self.plugins.pop(plugin_name)
            try:
                plugin_instance.unload()
            except Exception as e:
                print(f"Error during unload() method of plugin {plugin_name}: {e}")
        else:
            print(f"Plugin '{plugin_name}' not found.")

    def get_plugin(self, plugin_name: str) -> LockdoorPlugin | None:
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> list[str]:
        return list(self.plugins.keys())

# Example Usage (Optional - for testing, can be removed or put in a test file)
if __name__ == '__main__':
    manager = PluginManager()
    # Assume 'plugins' directory exists at the same level as this script's execution path
    # or adjust the path accordingly.
    # For example, if running from the root of the project:
    # manager.discover_plugins("plugins")
    # If this file is in src/plugin_framework_core and plugins is at root:
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root = os.path.dirname(os.path.dirname(current_dir)) # up two levels
    # plugins_dir = os.path.join(project_root, "plugins")
    # manager.discover_plugins(plugins_dir)

    # print("Loaded plugins:", manager.list_plugins())

    # To test this, you would need to:
    # 1. Create a 'plugins' directory.
    # 2. Create a sample plugin file in 'plugins', e.g., 'my_plugin.py' with a class
    #    that inherits from LockdoorPlugin and implements get_name, get_description.
    # Example my_plugin.py:
    # from plugin_framework_core.plugin_interface import LockdoorPlugin
    # class MyTestPlugin(LockdoorPlugin):
    #     def get_name(self) -> str: return "Test Plugin"
    #     def get_description(self) -> str: return "A simple test plugin."
    #     def load(self) -> None: print("MyTestPlugin Loaded")
    #     def unload(self) -> None: print("MyTestPlugin Unloaded")
    pass
