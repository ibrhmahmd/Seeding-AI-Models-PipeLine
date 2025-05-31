"""
Logger implementation for the AI Model Seeding Pipeline.

This module provides a concrete implementation of the ILogger interface
using loguru for enhanced logging capabilities.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from loguru import logger

from pipeline.interfaces import ILogger
from pipeline.config import get_config


class PipelineLogger(ILogger):
    """
    Logger implementation using loguru for the AI Model Seeding Pipeline.
    
    Features:
    - Supports both console and file logging
    - Configurable log levels
    - Includes timestamps and context information
    - Rotation of log files
    """
    
    def __init__(self, component_name: str = "Pipeline", log_file: Optional[str] = None, 
                log_level: str = "INFO", console: bool = True, file: bool = True):
        """
        Initialize the logger.
        
        Args:
            component_name: Name of the component using this logger.
            log_file: Path to the log file. If None, uses the path from config.
            log_level: Minimum log level to display (DEBUG, INFO, WARNING, ERROR).
            console: Whether to log to console.
            file: Whether to log to file.
        """
        self.component_name = component_name
        self.config = get_config()
        
        # Configure log format
        self.format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[component]} | {message}"
        
        # Remove default logger
        logger.remove()
        
        # Add console logger if enabled
        if console:
            logger.configure(extra={"component": component_name})
            logger.add(
                sys.stderr,
                format=self.format,
                level=log_level,
                colorize=True
            )
        
        # Add file logger if enabled
        if file:
            if log_file is None:
                # Use config or default
                log_file = self.config.log_file
            
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_file,
                format=self.format,
                level=log_level,
                rotation="10 MB",  # Rotate when file reaches 10MB
                retention=10,      # Keep 10 log files
                compression="zip"  # Compress rotated logs
            )
        
        self.logger = logger.bind(component=component_name)
    
    def info(self, message: str) -> None:
        """Log an informational message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)
    
    def create_child(self, component_name: str) -> 'PipelineLogger':
        """
        Create a child logger for a subcomponent.
        
        Args:
            component_name: Name of the subcomponent.
            
        Returns:
            A new logger instance for the subcomponent.
        """
        return PipelineLogger(
            component_name=f"{self.component_name}.{component_name}",
            log_file=None,  # Use same file as parent
            log_level=self.logger.level,
            console=False,  # Don't add another console handler
            file=False      # Don't add another file handler
        )


# Create a default logger instance
default_logger = PipelineLogger()


def get_logger(component_name: str = "Pipeline") -> PipelineLogger:
    """
    Get a logger instance.
    
    Args:
        component_name: Name of the component using this logger.
        
    Returns:
        A configured logger instance.
    """
    if component_name == "Pipeline":
        return default_logger
    return default_logger.create_child(component_name)


if __name__ == "__main__":
    # Test the logger
    logger = get_logger("LoggerTest")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test child logger
    child_logger = logger.create_child("Child")
    child_logger.info("This is a message from a child logger")
