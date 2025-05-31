"""
TagMapper component for the AI Model Seeding Pipeline.

This module provides implementations of the ITagMapper interface
for mapping tag names to tag IDs.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pipeline.base import BaseComponent, BaseModelReader, BaseModelWriter
from pipeline.interfaces import ILogger, IModelReader, IModelWriter, ITagMapper
from pipeline.logger import get_logger


class BaseTagMapper(BaseComponent, ITagMapper):
    """
    Base implementation of the ITagMapper interface.
    
    Provides common functionality for all tag mappers.
    """
    
    def __init__(self, logger: Optional[ILogger] = None, reader: Optional[IModelReader] = None, 
                writer: Optional[IModelWriter] = None):
        """
        Initialize the tag mapper.
        
        Args:
            logger: Logger for logging events. If None, a default logger is used.
            reader: Reader for loading models. If None, a default reader is used.
            writer: Writer for saving tagged models. If None, a default writer is used.
        """
        super().__init__(logger or get_logger("TagMapper"))
        self.reader = reader or BaseModelReader(self.logger)
        self.writer = writer or BaseModelWriter(self.logger)
    
    def map_tags(self, model_data: Dict[str, Any], tag_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map tags to a model.
        
        Args:
            model_data: Dictionary containing the model data.
            tag_map: Mapping of tag names to tag IDs.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - tagged_model: Dictionary with tagged model data
            - error: Error information if not successful
        """
        if not self.validate_input(model_data=model_data, tag_map=tag_map):
            return {
                "success": False,
                "error": {"message": "Invalid input for tag mapping"}
            }
        
        try:
            return self._map_tags_impl(model_data, tag_map)
        except Exception as e:
            self.logger.error(f"Error mapping tags: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Tag mapping error: {str(e)}", "type": type(e).__name__}
            }
    
    def _map_tags_impl(self, model_data: Dict[str, Any], tag_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of tag mapping logic.
        
        This should be overridden by subclasses.
        
        Args:
            model_data: Dictionary containing the model data.
            tag_map: Mapping of tag names to tag IDs.
            
        Returns:
            Dictionary containing tag mapping results.
            
        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses must implement _map_tags_impl")
    
    def map_directory(self, input_dir: Union[str, Path], output_dir: Union[str, Path], 
                    tag_map_file: Union[str, Path]) -> Dict[str, Any]:
        """
        Map tags for all models in a directory.
        
        Args:
            input_dir: Directory containing model files to tag.
            output_dir: Directory to save tagged models.
            tag_map_file: Path to the tag mapping file.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - tagged_models: List of paths to tagged model files
            - error: Error information if not successful
        """
        if not self.validate_input(input_dir=input_dir, output_dir=output_dir, tag_map_file=tag_map_file):
            return {
                "success": False,
                "error": {"message": "Invalid input for directory tag mapping"}
            }
        
        try:
            in_dir = Path(input_dir)
            if not in_dir.exists() or not in_dir.is_dir():
                return {
                    "success": False,
                    "error": {"message": f"Input directory not found: {in_dir}"}
                }
                
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            
            tag_map_path = Path(tag_map_file)
            if not tag_map_path.exists():
                return {
                    "success": False,
                    "error": {"message": f"Tag map file not found: {tag_map_path}"}
                }
                
            # Load tag map
            try:
                tag_map = self.reader.read_model(tag_map_path)
                self.logger.info(f"Loaded tag map with {len(tag_map)} entries from {tag_map_path}")
            except Exception as e:
                self.logger.error(f"Error loading tag map from {tag_map_path}: {str(e)}")
                return {
                    "success": False,
                    "error": {"message": f"Error loading tag map: {str(e)}", "type": type(e).__name__}
                }
            
            # Find all JSON files in the input directory
            model_files = list(in_dir.glob("*.json"))
            
            if not model_files:
                self.logger.warning(f"No model files found in {in_dir}")
                return {
                    "success": True,
                    "tagged_models": []
                }
            
            # Process each file
            tagged_models = []
            failed_models = []
            
            for model_file in model_files:
                try:
                    # Read the model data
                    model_data = self.reader.read_model(model_file)
                    
                    # Map tags
                    result = self.map_tags(model_data, tag_map)
                    
                    if not result["success"]:
                        self.logger.warning(f"Failed to map tags for {model_file.name}: {result.get('error', {}).get('message', 'Unknown error')}")
                        failed_models.append(str(model_file))
                        continue
                    
                    # Write the tagged model
                    tagged_model = result["tagged_model"]
                    output_file = out_dir / f"{model_file.stem}_tagged.json"
                    output_path = self.writer.write_model(tagged_model, output_file)
                    tagged_models.append(output_path)
                    
                    self.logger.info(f"Tagged {model_file.name} -> {output_path}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing {model_file}: {str(e)}")
                    failed_models.append(str(model_file))
            
            self.logger.info(f"Tagged {len(tagged_models)} models. Failed: {len(failed_models)}")
            
            result = {
                "success": len(failed_models) == 0,
                "tagged_models": [str(path) for path in tagged_models]
            }
            
            if failed_models:
                result["failed_models"] = failed_models
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error mapping directory: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Directory tag mapping error: {str(e)}", "type": type(e).__name__}
            }
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters.
        
        Args:
            **kwargs: Input parameters to validate.
            
        Returns:
            True if input is valid, False otherwise.
        """
        # Validate model_data if provided
        if 'model_data' in kwargs:
            model_data = kwargs['model_data']
            if not isinstance(model_data, dict):
                self.logger.error("Model data must be a dictionary")
                return False
        
        # Validate tag_map if provided
        if 'tag_map' in kwargs:
            tag_map = kwargs['tag_map']
            if not isinstance(tag_map, dict):
                self.logger.error("Tag map must be a dictionary")
                return False
        
        # Validate input_dir if provided
        if 'input_dir' in kwargs:
            input_dir = kwargs['input_dir']
            if not input_dir:
                self.logger.error("Input directory is required")
                return False
        
        # Validate output_dir if provided
        if 'output_dir' in kwargs:
            output_dir = kwargs['output_dir']
            if not output_dir:
                self.logger.error("Output directory is required")
                return False
        
        # Validate tag_map_file if provided
        if 'tag_map_file' in kwargs:
            tag_map_file = kwargs['tag_map_file']
            if not tag_map_file:
                self.logger.error("Tag map file is required")
                return False
        
        return True


class SimpleTagMapper(BaseTagMapper):
    """
    Simple implementation of tag mapping.
    
    Maps tag names to tag IDs based on a tag map dictionary.
    """
    
    def _map_tags_impl(self, model_data: Dict[str, Any], tag_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map tags to a model.
        
        Args:
            model_data: Dictionary containing the model data.
            tag_map: Mapping of tag names to tag IDs.
            
        Returns:
            Dictionary containing tag mapping results.
        """
        model_name = model_data.get('name', 'unknown')
        self.logger.info(f"Mapping tags for model '{model_name}'")
        
        # Create a copy of the model data to avoid modifying the original
        tagged_model = model_data.copy()
        
        # Get tags from model
        tags = tagged_model.get('tags', [])
        
        if not tags:
            self.logger.warning(f"No tags found in model '{model_name}'")
            tagged_model['tagIds'] = []
            
            return {
                "success": True,
                "tagged_model": tagged_model
            }
        
        # Normalize tags (ensure they're strings)
        normalized_tags = [str(tag).lower() for tag in tags]
        
        # Map tags to IDs
        tag_ids = []
        unmapped_tags = []
        
        for tag in normalized_tags:
            if tag in tag_map:
                tag_ids.append(tag_map[tag])
            else:
                unmapped_tags.append(tag)
        
        if unmapped_tags:
            self.logger.warning(f"Unmapped tags for '{model_name}': {', '.join(unmapped_tags)}")
        
        # Store tag IDs in model
        tagged_model['tagIds'] = tag_ids
        
        self.logger.info(f"Mapped {len(tag_ids)} tags for model '{model_name}'")
        
        return {
            "success": True,
            "tagged_model": tagged_model
        }


class FallbackTagMapper(BaseTagMapper):
    """
    Tag mapper with fallback strategies.
    
    Tries multiple strategies to map tags to IDs:
    1. Direct mapping from tag map
    2. Substring matching
    3. Fuzzy matching
    """
    
    def __init__(self, auto_create_tags: bool = False, **kwargs):
        """
        Initialize the fallback tag mapper.
        
        Args:
            auto_create_tags: Whether to automatically create tags not found in the tag map.
            **kwargs: Additional arguments to pass to the parent constructor.
        """
        super().__init__(**kwargs)
        self.auto_create_tags = auto_create_tags
        self.next_tag_id = 1000  # Starting ID for newly created tags
    
    def _map_tags_impl(self, model_data: Dict[str, Any], tag_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map tags to a model using multiple fallback strategies.
        
        Args:
            model_data: Dictionary containing the model data.
            tag_map: Mapping of tag names to tag IDs.
            
        Returns:
            Dictionary containing tag mapping results.
        """
        model_name = model_data.get('name', 'unknown')
        self.logger.info(f"Mapping tags for model '{model_name}' with fallback strategy")
        
        # Create a copy of the model data to avoid modifying the original
        tagged_model = model_data.copy()
        
        # Get tags from model
        tags = tagged_model.get('tags', [])
        
        if not tags:
            self.logger.warning(f"No tags found in model '{model_name}'")
            tagged_model['tagIds'] = []
            
            return {
                "success": True,
                "tagged_model": tagged_model
            }
        
        # Normalize tags (ensure they're strings)
        normalized_tags = [str(tag).lower() for tag in tags]
        
        # Create a working copy of the tag map
        working_tag_map = tag_map.copy()
        
        # Track the highest tag ID for auto-creation
        if self.auto_create_tags:
            existing_ids = [int(id) for id in tag_map.values() if isinstance(id, (int, str)) and str(id).isdigit()]
            if existing_ids:
                self.next_tag_id = max(existing_ids) + 1
        
        # Map tags to IDs
        tag_ids = []
        unmapped_tags = []
        
        for tag in normalized_tags:
            # Strategy 1: Direct mapping
            if tag in working_tag_map:
                tag_ids.append(working_tag_map[tag])
                continue
            
            # Strategy 2: Substring matching
            found = False
            for map_tag, map_id in working_tag_map.items():
                if tag in map_tag or map_tag in tag:
                    tag_ids.append(map_id)
                    self.logger.info(f"Mapped '{tag}' to '{map_tag}' (ID: {map_id}) via substring matching")
                    found = True
                    break
            
            if found:
                continue
            
            # If we got here, the tag couldn't be mapped
            if self.auto_create_tags:
                # Create a new tag ID
                new_id = self.next_tag_id
                self.next_tag_id += 1
                
                working_tag_map[tag] = new_id
                tag_ids.append(new_id)
                
                self.logger.info(f"Created new tag '{tag}' with ID {new_id}")
            else:
                unmapped_tags.append(tag)
        
        if unmapped_tags:
            self.logger.warning(f"Unmapped tags for '{model_name}': {', '.join(unmapped_tags)}")
        
        # Store tag IDs in model
        tagged_model['tagIds'] = tag_ids
        
        self.logger.info(f"Mapped {len(tag_ids)} tags for model '{model_name}'")
        
        return {
            "success": True,
            "tagged_model": tagged_model
        }
