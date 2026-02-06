
from typing import Any, Dict


class BaseTool:
    """Base class for all agent tools"""
    
    def get_name(self) -> str:
        """Returns the tool name"""
        raise NotImplementedError
    
    def get_description(self) -> str:
        """Returns what the tool does"""
        raise NotImplementedError
    
    def get_parameters(self) -> Dict[str, Any]:
        """Returns the parameter schema for the tool"""
        raise NotImplementedError
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Executes the tool with given parameters"""
        raise NotImplementedError