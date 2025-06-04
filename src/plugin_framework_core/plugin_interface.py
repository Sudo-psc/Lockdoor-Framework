from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypedDict, Optional

# Using TypedDict for a more structured definition of actions and parameters
class ActionParameter(TypedDict, total=False):
    name: str
    description: Optional[str]
    type: Optional[str]  # e.g., 'string', 'integer', 'boolean', 'file'
    required: Optional[bool]

class Action(TypedDict):
    name: str
    description: str
    parameters: List[ActionParameter]

class LockdoorPlugin(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass

    def load(self) -> None:
        # Optional: Called when the plugin is loaded
        # print(f"Plugin {self.get_name()} loaded.") # Commented out default print
        pass

    def unload(self) -> None:
        # Optional: Called when the plugin is unloaded
        # print(f"Plugin {self.get_name()} unloaded.") # Commented out default print
        pass

    @abstractmethod
    def get_actions(self) -> List[Action]:
        """Returns a list of actions this plugin provides."""
        pass

    @abstractmethod
    def execute_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        """
        Executes a specific action offered by the plugin.

        Args:
            action_name: The name of the action to execute.
            params: A dictionary of parameters for the action.

        Returns:
            The result of the action, type depends on the action.
        """
        pass
