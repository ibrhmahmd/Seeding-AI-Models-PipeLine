"""
Extractor component for the AI Model Seeding Pipeline.

This module provides implementations of the IExtractor interface
for extracting model data from various sources.
"""

import json
import os
from pathlib import Path
import requests
from typing import Any, Dict, List, Optional, Union

from pipeline.base import BaseComponent, BaseModelWriter
from pipeline.interfaces import IExtractor, ILogger, IModelWriter
from pipeline.logger import get_logger


class BaseExtractor(BaseComponent, IExtractor):
    """
    Base implementation of the IExtractor interface.
    
    Provides common functionality for all extractors.
    """
    
    def __init__(self, logger: Optional[ILogger] = None, writer: Optional[IModelWriter] = None):
        """
        Initialize the extractor.
        
        Args:
            logger: Logger for logging events. If None, a default logger is used.
            writer: Writer for saving extracted models. If None, a default writer is used.
        """
        super().__init__(logger or get_logger("Extractor"))
        self.writer = writer or BaseModelWriter(self.logger)
    
    def extract_from_source(self, source_config: Dict[str, Any], output_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract models from a source and save to the output directory.
        
        This is a template method that should be implemented by subclasses.
        
        Args:
            source_config: Configuration for the source.
            output_dir: Directory to save extracted models.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - extracted_models: List of paths to extracted model files
            - error: Error information if not successful
        """
        if not self.validate_input(source_config=source_config, output_dir=output_dir):
            return {
                "success": False,
                "error": {"message": "Invalid input for extraction"}
            }
        
        try:
            return self._extract_from_source_impl(source_config, output_dir)
        except Exception as e:
            self.logger.error(f"Error extracting from source: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Extraction error: {str(e)}", "type": type(e).__name__}
            }
    
    def _extract_from_source_impl(self, source_config: Dict[str, Any], output_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Implementation of source extraction logic.
        
        This should be overridden by subclasses.
        
        Args:
            source_config: Configuration for the source.
            output_dir: Directory to save extracted models.
            
        Returns:
            Dictionary containing extraction results.
            
        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses must implement _extract_from_source_impl")
    
    def extract_from_file(self, file_path: Union[str, Path], output_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract model data from a file and save to the output directory.
        
        Args:
            file_path: Path to the file containing model data.
            output_dir: Directory to save extracted models.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - extracted_models: List of paths to extracted model files
            - error: Error information if not successful
        """
        if not self.validate_input(file_path=file_path, output_dir=output_dir):
            return {
                "success": False,
                "error": {"message": "Invalid input for file extraction"}
            }
        
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": {"message": f"File not found: {path}"}
                }
                
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Ensure output directory exists
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            
            # Write extracted model to output file
            output_file = out_dir / f"{path.stem}_raw.json"
            output_path = self.writer.write_model(data, output_file)
            
            self.logger.info(f"Extracted model from {path} to {output_path}")
            return {
                "success": True,
                "extracted_models": [output_path]
            }
        except Exception as e:
            self.logger.error(f"Error extracting from file {file_path}: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"File extraction error: {str(e)}", "type": type(e).__name__}
            }
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters.
        
        Args:
            **kwargs: Input parameters to validate.
            
        Returns:
            True if input is valid, False otherwise.
        """
        # Validate output_dir if provided
        if 'output_dir' in kwargs:
            output_dir = kwargs['output_dir']
            if not output_dir:
                self.logger.error("Output directory is required")
                return False
        
        # Validate file_path if provided
        if 'file_path' in kwargs:
            file_path = kwargs['file_path']
            if not file_path:
                self.logger.error("File path is required")
                return False
                
        # Validate source_config if provided
        if 'source_config' in kwargs:
            source_config = kwargs['source_config']
            if not isinstance(source_config, dict):
                self.logger.error("Source configuration must be a dictionary")
                return False
        
        return True


class OllamaExtractor(BaseExtractor):
    """
    Extractor for Ollama models.
    
    Extracts model metadata from the Ollama API.
    """
    
    def _extract_from_source_impl(self, source_config: Dict[str, Any], output_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract models from Ollama API.
        
        Args:
            source_config: Configuration for the Ollama API.
                Must contain:
                - api_url: URL of the Ollama API.
                May contain:
                - timeout: Request timeout in seconds.
            output_dir: Directory to save extracted models.
            
        Returns:
            Dictionary containing extraction results.
        """
        # Validate Ollama-specific config
        if 'api_url' not in source_config:
            return {
                "success": False,
                "error": {"message": "Ollama API URL is required in source configuration"}
            }
        
        api_url = source_config['api_url']
        timeout = source_config.get('timeout', 30)
        
        self.logger.info(f"Extracting models from Ollama API at {api_url}")
        
        try:
            # Ensure output directory exists
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            
            # Request models from Ollama API
            response = requests.get(f"{api_url}/api/tags", timeout=timeout)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": {
                        "message": f"Ollama API request failed with status {response.status_code}",
                        "response": response.text
                    }
                }
            
            # Parse response
            data = response.json()
            
            if 'models' not in data:
                return {
                    "success": False,
                    "error": {"message": "Unexpected response format from Ollama API"}
                }
            
            # Process and save each model
            extracted_models = []
            for model in data['models']:
                # Create a standardized model object
                model_data = {
                    "name": model.get('name', ''),
                    "modelId": f"ollama-{model.get('name', '')}",
                    "description": model.get('description', ''),
                    "parameters": {},
                    "tags": ["ollama"],
                    "metadata": {
                        "size": model.get('size', 0),
                        "modified_at": model.get('modified_at', ''),
                        "source": "ollama"
                    }
                }
                
                # Add appropriate tags based on model name
                model_name = model.get('name', '').lower()
                
                if 'llama' in model_name:
                    model_data['tags'].append('llama')
                if 'mistral' in model_name:
                    model_data['tags'].append('mistral')
                if 'code' in model_name or 'codellama' in model_name:
                    model_data['tags'].append('code')
                    
                # Write to file
                output_file = out_dir / f"{model_data['name']}_raw.json"
                output_path = self.writer.write_model(model_data, output_file)
                extracted_models.append(output_path)
            
            self.logger.info(f"Extracted {len(extracted_models)} models from Ollama API")
            return {
                "success": True,
                "extracted_models": extracted_models
            }
        except requests.RequestException as e:
            self.logger.error(f"Request error extracting from Ollama API: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Ollama API request error: {str(e)}", "type": "RequestError"}
            }
        except Exception as e:
            self.logger.error(f"Error extracting from Ollama API: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Ollama extraction error: {str(e)}", "type": type(e).__name__}
            }
            
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters for Ollama extractor.
        
        Args:
            **kwargs: Input parameters to validate.
            
        Returns:
            True if input is valid, False otherwise.
        """
        # First call parent validation
        if not super().validate_input(**kwargs):
            return False
            
        # Validate Ollama-specific parameters
        if 'source_config' in kwargs:
            source_config = kwargs['source_config']
            if 'api_url' not in source_config:
                self.logger.error("Ollama API URL is required in source configuration")
                return False
        
        return True


class JsonFileExtractor(BaseExtractor):
    """
    Extractor for JSON files containing model data.
    
    Extracts model metadata from JSON files.
    """
    
    def _extract_from_source_impl(self, source_config: Dict[str, Any], output_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract models from JSON files.
        
        Args:
            source_config: Configuration for the JSON file source.
                Must contain:
                - input_dir: Directory containing JSON files.
                May contain:
                - pattern: File pattern to match (default: "*.json").
            output_dir: Directory to save extracted models.
            
        Returns:
            Dictionary containing extraction results.
        """
        # Validate JSON file source config
        if 'input_dir' not in source_config:
            return {
                "success": False,
                "error": {"message": "Input directory is required in source configuration"}
            }
        
        input_dir = source_config['input_dir']
        pattern = source_config.get('pattern', "*.json")
        
        self.logger.info(f"Extracting models from JSON files in {input_dir}")
        
        try:
            # Ensure input and output directories exist
            in_dir = Path(input_dir)
            if not in_dir.exists() or not in_dir.is_dir():
                return {
                    "success": False,
                    "error": {"message": f"Input directory not found: {in_dir}"}
                }
                
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            
            # Find all matching files
            files = list(in_dir.glob(pattern))
            
            if not files:
                self.logger.warning(f"No files matching '{pattern}' found in {in_dir}")
                return {
                    "success": True,
                    "extracted_models": []
                }
            
            # Process each file
            extracted_models = []
            for file_path in files:
                result = self.extract_from_file(file_path, output_dir)
                if result["success"]:
                    extracted_models.extend(result["extracted_models"])
                else:
                    self.logger.warning(f"Failed to extract from {file_path}: {result.get('error', {}).get('message', 'Unknown error')}")
            
            self.logger.info(f"Extracted {len(extracted_models)} models from JSON files")
            return {
                "success": True,
                "extracted_models": extracted_models
            }
        except Exception as e:
            self.logger.error(f"Error extracting from JSON files: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"JSON file extraction error: {str(e)}", "type": type(e).__name__}
            }
            
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters for JSON file extractor.
        
        Args:
            **kwargs: Input parameters to validate.
            
        Returns:
            True if input is valid, False otherwise.
        """
        # First call parent validation
        if not super().validate_input(**kwargs):
            return False
            
        # Validate JSON file-specific parameters
        if 'source_config' in kwargs:
            source_config = kwargs['source_config']
            if 'input_dir' not in source_config:
                self.logger.error("Input directory is required in source configuration")
                return False
        
        return True
