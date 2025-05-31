"""
Base classes for AI Model Seeding Pipeline components.

This module provides base implementations of the interfaces defined in interfaces.py,
offering shared functionality that concrete component implementations can leverage.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from .interfaces import (
    IComponent, IModelReader, IModelWriter, ILogger
)


class BaseLogger(ILogger):
    """Base implementation of the ILogger interface."""
    
    def info(self, message: str) -> None:
        """Log an informational message."""
        logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log an error message."""
        logger.error(message)
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        logger.debug(message)


class BaseModelReader(IModelReader):
    """Base implementation of the IModelReader interface."""
    
    def __init__(self, logger: Optional[ILogger] = None):
        """
        Initialize the model reader.
        
        Args:
            logger: Logger for logging events. If None, a default logger is used.
        """
        self.logger = logger or BaseLogger()
    
    def read_model(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read model data from a JSON file.
        
        Args:
            file_path: Path to the model file.
            
        Returns:
            Dictionary containing the model data.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a valid JSON file.
        """
        path = Path(file_path)
        if not path.exists():
            self.logger.error(f"File not found: {path}")
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.debug(f"Successfully read model from {path}")
                return data
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {path}: {str(e)}")
            raise ValueError(f"Invalid JSON in {path}: {str(e)}")
    
    def list_models(self, directory: Union[str, Path]) -> List[Path]:
        """
        List available JSON model files in a directory.
        
        Args:
            directory: Directory to search for model files.
            
        Returns:
            List of paths to model files.
        """
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            self.logger.error(f"Directory not found: {dir_path}")
            return []
        
        model_files = list(dir_path.glob("*.json"))
        self.logger.info(f"Found {len(model_files)} model files in {dir_path}")
        return model_files


class BaseModelWriter(IModelWriter):
    """Base implementation of the IModelWriter interface."""
    
    def __init__(self, logger: Optional[ILogger] = None):
        """
        Initialize the model writer.
        
        Args:
            logger: Logger for logging events. If None, a default logger is used.
        """
        self.logger = logger or BaseLogger()
    
    def write_model(self, model_data: Dict[str, Any], file_path: Union[str, Path]) -> Path:
        """
        Write model data to a JSON file.
        
        Args:
            model_data: Dictionary containing the model data.
            file_path: Path where the model file should be written.
            
        Returns:
            Path to the written file.
            
        Raises:
            IOError: If the file cannot be written.
        """
        path = Path(file_path)
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, indent=2, ensure_ascii=False)
                self.logger.debug(f"Successfully wrote model to {path}")
                return path
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to write to {path}: {str(e)}")
            raise IOError(f"Failed to write to {path}: {str(e)}")


class BaseComponent(IComponent):
    """Base implementation of the IComponent interface."""
    
    def __init__(self, logger: Optional[ILogger] = None):
        """
        Initialize the component.
        
        Args:
            logger: Logger for logging events. If None, a default logger is used.
        """
        self.logger = logger or BaseLogger()
        self.last_error = None
    
    def process(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Process input data and return results.
        
        This is a template method that should be overridden by subclasses.
        
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - result: The processing result if successful
            - error: Error information if not successful
        """
        try:
            if not self.validate_input(*args, **kwargs):
                self.last_error = {"message": "Invalid input", "args": args, "kwargs": kwargs}
                return {
                    "success": False,
                    "error": self.last_error
                }
            
            # Actual processing should be implemented by subclasses
            result = self._process_implementation(*args, **kwargs)
            
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            self.last_error = {"message": str(e), "type": type(e).__name__}
            self.logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return {
                "success": False,
                "error": self.last_error
            }
    
    def _process_implementation(self, *args: Any, **kwargs: Any) -> Any:
        """
        Implementation of the processing logic.
        
        This should be overridden by subclasses.
        
        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses must implement _process_implementation")
    
    def validate_input(self, *args: Any, **kwargs: Any) -> bool:
        """
        Validate that the input meets the component's requirements.
        
        This should be overridden by subclasses.
        
        Returns:
            True if input is valid, False otherwise.
        """
        # Default implementation always returns True
        # Subclasses should override this with proper validation
        return True


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory.
        
    Returns:
        Path object representing the directory.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
