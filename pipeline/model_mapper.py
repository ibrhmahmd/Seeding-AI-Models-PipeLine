"""
ModelMapper component for the AI Model Seeding Pipeline.

This module provides implementations of the IModelMapper interface
for mapping models to the API schema.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pipeline.base import BaseComponent, BaseModelReader, BaseModelWriter
from pipeline.interfaces import ILogger, IModelMapper, IModelReader, IModelWriter
from pipeline.logger import get_logger


class BaseModelMapper(BaseComponent, IModelMapper):
    """
    Base implementation of the IModelMapper interface.
    
    Provides common functionality for all model mappers.
    """
    
    def __init__(self, logger: Optional[ILogger] = None, reader: Optional[IModelReader] = None, 
                writer: Optional[IModelWriter] = None):
        """
        Initialize the model mapper.
        
        Args:
            logger: Logger for logging events. If None, a default logger is used.
            reader: Reader for loading models. If None, a default reader is used.
            writer: Writer for saving mapped models. If None, a default writer is used.
        """
        super().__init__(logger or get_logger("ModelMapper"))
        self.reader = reader or BaseModelReader(self.logger)
        self.writer = writer or BaseModelWriter(self.logger)
    
    def map_to_api_schema(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a model to the API schema.
        
        Args:
            model_data: Dictionary containing the model data.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - mapped_model: Dictionary with API-ready model data
            - error: Error information if not successful
        """
        if not self.validate_input(model_data=model_data):
            return {
                "success": False,
                "error": {"message": "Invalid input for model mapping"}
            }
        
        try:
            return self._map_to_api_schema_impl(model_data)
        except Exception as e:
            self.logger.error(f"Error mapping model to API schema: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Model mapping error: {str(e)}", "type": type(e).__name__}
            }
    
    def _map_to_api_schema_impl(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of model mapping logic.
        
        This should be overridden by subclasses.
        
        Args:
            model_data: Dictionary containing the model data.
            
        Returns:
            Dictionary containing model mapping results.
            
        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses must implement _map_to_api_schema_impl")
    
    def validate_api_model(self, api_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a model meets the API requirements.
        
        Args:
            api_model: Dictionary containing the API-ready model data.
            
        Returns:
            Dictionary containing:
            - valid: Boolean indicating if the model is valid
            - errors: List of validation errors, if any
        """
        errors = []
        
        # Check required fields
        required_fields = ['modelId', 'name', 'description']
        for field in required_fields:
            if field not in api_model or not api_model[field]:
                errors.append(f"Missing required field: {field}")
        
        # Check tag IDs
        if 'tagIds' not in api_model or not isinstance(api_model['tagIds'], list):
            errors.append("Missing or invalid tagIds (must be a list)")
        
        # Check reference link
        if 'referenceLink' not in api_model or not api_model['referenceLink']:
            errors.append("Missing referenceLink")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def map_directory(self, input_dir: Union[str, Path], output_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Map all models in a directory to the API schema.
        
        Args:
            input_dir: Directory containing model files to map.
            output_dir: Directory to save mapped models.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - mapped_models: List of paths to mapped model files
            - error: Error information if not successful
        """
        if not self.validate_input(input_dir=input_dir, output_dir=output_dir):
            return {
                "success": False,
                "error": {"message": "Invalid input for directory mapping"}
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
            
            # Find all JSON files in the input directory
            model_files = list(in_dir.glob("*.json"))
            
            if not model_files:
                self.logger.warning(f"No model files found in {in_dir}")
                return {
                    "success": True,
                    "mapped_models": []
                }
            
            # Process each file
            mapped_models = []
            failed_models = []
            
            for model_file in model_files:
                try:
                    # Read the model data
                    model_data = self.reader.read_model(model_file)
                    
                    # Map the model
                    result = self.map_to_api_schema(model_data)
                    
                    if not result["success"]:
                        self.logger.warning(f"Failed to map {model_file.name}: {result.get('error', {}).get('message', 'Unknown error')}")
                        failed_models.append(str(model_file))
                        continue
                    
                    # Validate the mapped model
                    mapped_model = result["mapped_model"]
                    validation = self.validate_api_model(mapped_model)
                    
                    if not validation["valid"]:
                        error_msg = "; ".join(validation["errors"])
                        self.logger.warning(f"Validation failed for {model_file.name}: {error_msg}")
                        failed_models.append(str(model_file))
                        continue
                    
                    # Write the mapped model
                    output_file = out_dir / f"{model_file.stem}_api_payload.json"
                    output_path = self.writer.write_model(mapped_model, output_file)
                    mapped_models.append(output_path)
                    
                    self.logger.info(f"Mapped {model_file.name} -> {output_path}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing {model_file}: {str(e)}")
                    failed_models.append(str(model_file))
            
            self.logger.info(f"Mapped {len(mapped_models)} models. Failed: {len(failed_models)}")
            
            result = {
                "success": len(failed_models) == 0,
                "mapped_models": [str(path) for path in mapped_models]
            }
            
            if failed_models:
                result["failed_models"] = failed_models
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error mapping directory: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Directory mapping error: {str(e)}", "type": type(e).__name__}
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
        
        return True


class StandardModelMapper(BaseModelMapper):
    """
    Standard implementation of the model mapper.
    
    Maps models to the API schema with standard transformations.
    """
    
    def __init__(self, placeholder_url: str = "https://example.com/placeholder", **kwargs):
        """
        Initialize the standard model mapper.
        
        Args:
            placeholder_url: URL to use when a model has no reference link.
            **kwargs: Additional arguments to pass to the parent constructor.
        """
        super().__init__(**kwargs)
        self.placeholder_url = placeholder_url
    
    def _map_to_api_schema_impl(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a model to the API schema.
        
        Args:
            model_data: Dictionary containing the model data.
            
        Returns:
            Dictionary containing mapping results.
        """
        model_name = model_data.get('name', 'unknown')
        self.logger.info(f"Mapping model '{model_name}' to API schema")
        
        # Create API model with required fields
        api_model = {
            "modelId": model_data.get('modelId', f"model-{model_name}"),
            "name": model_name,
            "displayName": model_data.get('display_name', self._generate_display_name(model_name)),
            "description": model_data.get('description', f"Model {model_name}"),
            "isActive": True,
            "version": "1.0"
        }
        
        # Add tag IDs if present
        if 'tagIds' in model_data and isinstance(model_data['tagIds'], list):
            api_model['tagIds'] = model_data['tagIds']
        elif 'tags' in model_data and isinstance(model_data['tags'], list):
            self.logger.warning(f"Model '{model_name}' has tags but no tagIds")
            api_model['tagIds'] = []
        else:
            api_model['tagIds'] = []
        
        # Add reference link if present, otherwise use placeholder
        if 'referenceLink' in model_data and model_data['referenceLink']:
            api_model['referenceLink'] = model_data['referenceLink']
        elif 'metadata' in model_data and 'huggingface' in model_data['metadata']:
            api_model['referenceLink'] = model_data['metadata']['huggingface'].get('url', self.placeholder_url)
        else:
            api_model['referenceLink'] = self.placeholder_url
            self.logger.warning(f"Using placeholder URL for model '{model_name}'")
        
        # Add parameters if present
        if 'parameters' in model_data:
            # Convert parameters to JSON string if they're a dictionary
            if isinstance(model_data['parameters'], dict):
                api_model['parameters'] = json.dumps(model_data['parameters'])
            else:
                api_model['parameters'] = str(model_data['parameters'])
        
        # Add timestamps
        current_time = datetime.now().isoformat()
        api_model['createdAt'] = current_time
        api_model['updatedAt'] = current_time
        
        self.logger.info(f"Successfully mapped model '{model_name}' to API schema")
        
        return {
            "success": True,
            "mapped_model": api_model
        }
    
    def _generate_display_name(self, name: str) -> str:
        """
        Generate a display name from a model name.
        
        Args:
            name: Model name.
            
        Returns:
            Human-readable display name.
        """
        # Replace hyphens and underscores with spaces
        display_name = name.replace('-', ' ').replace('_', ' ')
        
        # Title case the name
        display_name = ' '.join(word.capitalize() for word in display_name.split())
        
        return display_name
