"""
Archiver component for the AI Model Seeding Pipeline.

This module provides implementations of the IArchiver interface
for archiving processed files.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pipeline.base import BaseComponent
from pipeline.interfaces import IArchiver, ILogger
from pipeline.logger import get_logger


class BaseArchiver(BaseComponent, IArchiver):
    """
    Base implementation of the IArchiver interface.
    
    Provides common functionality for all archivers.
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        """
        Initialize the archiver.
        
        Args:
            logger: Logger for logging events. If None, a default logger is used.
        """
        super().__init__(logger or get_logger("Archiver"))
    
    def archive_file(self, file_path: Union[str, Path], archive_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Archive a single file.
        
        Args:
            file_path: Path to the file to archive.
            archive_dir: Directory to move the file to.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - archived_path: Path to the archived file
            - error: Error information if not successful
        """
        if not self.validate_input(file_path=file_path, archive_dir=archive_dir):
            return {
                "success": False,
                "error": {"message": "Invalid input for file archiving"}
            }
        
        try:
            return self._archive_file_impl(file_path, archive_dir)
        except Exception as e:
            self.logger.error(f"Error archiving file: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Archiving error: {str(e)}", "type": type(e).__name__}
            }
    
    def _archive_file_impl(self, file_path: Union[str, Path], archive_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Implementation of file archiving logic.
        
        This should be overridden by subclasses.
        
        Args:
            file_path: Path to the file to archive.
            archive_dir: Directory to move the file to.
            
        Returns:
            Dictionary containing archiving results.
            
        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses must implement _archive_file_impl")
    
    def archive_directory(self, input_dir: Union[str, Path], archive_dir: Union[str, Path], 
                        pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Archive all files in a directory.
        
        Args:
            input_dir: Directory containing files to archive.
            archive_dir: Directory to move the files to.
            pattern: Optional glob pattern to filter files.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - archived_files: List of paths to archived files
            - error: Error information if not successful
        """
        if not self.validate_input(input_dir=input_dir, archive_dir=archive_dir):
            return {
                "success": False,
                "error": {"message": "Invalid input for directory archiving"}
            }
        
        try:
            in_dir = Path(input_dir)
            if not in_dir.exists() or not in_dir.is_dir():
                return {
                    "success": False,
                    "error": {"message": f"Input directory not found: {in_dir}"}
                }
                
            # Find all files in the input directory
            if pattern:
                files = list(in_dir.glob(pattern))
            else:
                files = list(in_dir.glob("*"))
            
            if not files:
                self.logger.warning(f"No files found in {in_dir}")
                return {
                    "success": True,
                    "archived_files": []
                }
            
            # Process each file
            archived_files = []
            failed_files = []
            
            for file_path in files:
                if file_path.is_file():
                    result = self.archive_file(file_path, archive_dir)
                    
                    if result["success"]:
                        archived_files.append(str(result["archived_path"]))
                    else:
                        failed_files.append({
                            "file": str(file_path),
                            "error": result.get("error", {}).get("message", "Unknown error")
                        })
            
            self.logger.info(f"Archived {len(archived_files)} files. Failed: {len(failed_files)}")
            
            result = {
                "success": len(failed_files) == 0,
                "archived_files": archived_files
            }
            
            if failed_files:
                result["failed_files"] = failed_files
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error archiving directory: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Directory archiving error: {str(e)}", "type": type(e).__name__}
            }
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters.
        
        Args:
            **kwargs: Input parameters to validate.
            
        Returns:
            True if input is valid, False otherwise.
        """
        # Validate file_path if provided
        if 'file_path' in kwargs:
            file_path = kwargs['file_path']
            if not file_path:
                self.logger.error("File path is required")
                return False
        
        # Validate archive_dir if provided
        if 'archive_dir' in kwargs:
            archive_dir = kwargs['archive_dir']
            if not archive_dir:
                self.logger.error("Archive directory is required")
                return False
        
        # Validate input_dir if provided
        if 'input_dir' in kwargs:
            input_dir = kwargs['input_dir']
            if not input_dir:
                self.logger.error("Input directory is required")
                return False
        
        return True


class SimpleArchiver(BaseArchiver):
    """
    Simple implementation of the archiver.
    
    Archives files by moving them to the archive directory.
    """
    
    def _archive_file_impl(self, file_path: Union[str, Path], archive_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Archive a file by moving it to the archive directory.
        
        Args:
            file_path: Path to the file to archive.
            archive_dir: Directory to move the file to.
            
        Returns:
            Dictionary containing archiving results.
        """
        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "error": {"message": f"File not found: {path}"}
            }
        
        if not path.is_file():
            return {
                "success": False,
                "error": {"message": f"Not a file: {path}"}
            }
        
        # Ensure archive directory exists
        archive_path = Path(archive_dir)
        archive_path.mkdir(parents=True, exist_ok=True)
        
        # Determine destination file path
        dest_path = archive_path / path.name
        
        # Handle file name collision
        if dest_path.exists():
            # Add timestamp to file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = archive_path / f"{path.stem}_{timestamp}{path.suffix}"
        
        # Move the file
        shutil.move(str(path), str(dest_path))
        
        self.logger.info(f"Archived {path} to {dest_path}")
        
        return {
            "success": True,
            "archived_path": dest_path
        }


class OrganizedArchiver(BaseArchiver):
    """
    Archiver that organizes files into subdirectories.
    
    Archives files by organizing them into subdirectories based on date or other criteria.
    """
    
    def __init__(self, organize_by_date: bool = True, include_timestamp: bool = False, **kwargs):
        """
        Initialize the organized archiver.
        
        Args:
            organize_by_date: Whether to organize files into date-based subdirectories.
            include_timestamp: Whether to include a timestamp in the archived file name.
            **kwargs: Additional arguments to pass to the parent constructor.
        """
        super().__init__(**kwargs)
        self.organize_by_date = organize_by_date
        self.include_timestamp = include_timestamp
    
    def _archive_file_impl(self, file_path: Union[str, Path], archive_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Archive a file with organization.
        
        Args:
            file_path: Path to the file to archive.
            archive_dir: Directory to move the file to.
            
        Returns:
            Dictionary containing archiving results.
        """
        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "error": {"message": f"File not found: {path}"}
            }
        
        if not path.is_file():
            return {
                "success": False,
                "error": {"message": f"Not a file: {path}"}
            }
        
        # Determine the archive subdirectory
        archive_path = Path(archive_dir)
        
        if self.organize_by_date:
            # Create date-based subdirectory
            today = datetime.now().strftime("%Y-%m-%d")
            archive_path = archive_path / today
        
        # Ensure archive directory exists
        archive_path.mkdir(parents=True, exist_ok=True)
        
        # Determine destination file name
        if self.include_timestamp:
            timestamp = datetime.now().strftime("%H%M%S")
            dest_path = archive_path / f"{path.stem}_{timestamp}{path.suffix}"
        else:
            dest_path = archive_path / path.name
            
            # Handle file name collision
            if dest_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = archive_path / f"{path.stem}_{timestamp}{path.suffix}"
        
        # Move the file
        shutil.move(str(path), str(dest_path))
        
        self.logger.info(f"Archived {path} to {dest_path}")
        
        return {
            "success": True,
            "archived_path": dest_path
        }


class MetadataArchiver(BaseArchiver):
    """
    Archiver that stores metadata with archived files.
    
    Archives files and stores additional metadata about the archiving process.
    """
    
    def _archive_file_impl(self, file_path: Union[str, Path], archive_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Archive a file with metadata.
        
        Args:
            file_path: Path to the file to archive.
            archive_dir: Directory to move the file to.
            
        Returns:
            Dictionary containing archiving results.
        """
        path = Path(file_path)
        if not path.exists():
            return {
                "success": False,
                "error": {"message": f"File not found: {path}"}
            }
        
        if not path.is_file():
            return {
                "success": False,
                "error": {"message": f"Not a file: {path}"}
            }
        
        # Ensure archive directory exists
        archive_path = Path(archive_dir)
        archive_path.mkdir(parents=True, exist_ok=True)
        
        # Determine destination file path
        dest_path = archive_path / path.name
        
        # Handle file name collision
        if dest_path.exists():
            # Add timestamp to file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = archive_path / f"{path.stem}_{timestamp}{path.suffix}"
        
        # Create metadata
        metadata = {
            "original_path": str(path),
            "archived_path": str(dest_path),
            "archived_at": datetime.now().isoformat(),
            "file_size": path.stat().st_size,
            "file_name": path.name
        }
        
        # Try to extract model ID and name if it's a JSON file
        if path.suffix.lower() == '.json':
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        if 'modelId' in data:
                            metadata['modelId'] = data['modelId']
                        if 'name' in data:
                            metadata['modelName'] = data['name']
            except:
                # Ignore errors when trying to extract metadata
                pass
        
        # Move the file
        shutil.move(str(path), str(dest_path))
        
        # Save metadata file
        metadata_path = dest_path.with_suffix('.metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Archived {path} to {dest_path} with metadata")
        
        return {
            "success": True,
            "archived_path": dest_path,
            "metadata_path": metadata_path,
            "metadata": metadata
        }
