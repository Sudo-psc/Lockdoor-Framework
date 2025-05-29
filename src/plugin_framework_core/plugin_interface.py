from abc import ABC, abstractmethod

class LockdoorPlugin(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass

    def load(self) -> None:
        # Optional: Called when the plugin is loaded
        print(f"Plugin {self.get_name()} loaded.")
        pass

    def unload(self) -> None:
        # Optional: Called when the plugin is unloaded
        print(f"Plugin {self.get_name()} unloaded.")
        pass

    # Optional:
    # @abstractmethod
    # def execute(self, **kwargs) -> any:
    #     pass
