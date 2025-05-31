"""
Enricher component for the AI Model Seeding Pipeline.

This module provides implementations of the IEnricher interface
for enriching model data with additional metadata.
"""

import json
import os
from pathlib import Path
import requests
from typing import Any, Dict, List, Optional, Union

from pipeline.base import BaseComponent, BaseModelReader, BaseModelWriter
from pipeline.interfaces import IEnricher, ILogger, IModelReader, IModelWriter
from pipeline.logger import get_logger


class BaseEnricher(BaseComponent, IEnricher):
    """
    Base implementation of the IEnricher interface.
    
    Provides common functionality for all enrichers.
    """
    
    def __init__(self, logger: Optional[ILogger] = None, reader: Optional[IModelReader] = None, 
                writer: Optional[IModelWriter] = None):
        """
        Initialize the enricher.
        
        Args:
            logger: Logger for logging events. If None, a default logger is used.
            reader: Reader for loading models. If None, a default reader is used.
            writer: Writer for saving enriched models. If None, a default writer is used.
        """
        super().__init__(logger or get_logger("Enricher"))
        self.reader = reader or BaseModelReader(self.logger)
        self.writer = writer or BaseModelWriter(self.logger)
    
    def enrich_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a single model with additional metadata.
        
        This is a template method that should be implemented by subclasses.
        
        Args:
            model_data: Dictionary containing the model data.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - enriched_model: Dictionary with enriched model data
            - error: Error information if not successful
        """
        if not self.validate_input(model_data=model_data):
            return {
                "success": False,
                "error": {"message": "Invalid model data for enrichment"}
            }
        
        try:
            return self._enrich_model_impl(model_data)
        except Exception as e:
            self.logger.error(f"Error enriching model: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Enrichment error: {str(e)}", "type": type(e).__name__}
            }
    
    def _enrich_model_impl(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of model enrichment logic.
        
        This should be overridden by subclasses.
        
        Args:
            model_data: Dictionary containing the model data.
            
        Returns:
            Dictionary containing enrichment results.
            
        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses must implement _enrich_model_impl")
    
    def enrich_directory(self, input_dir: Union[str, Path], output_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Enrich all models in a directory.
        
        Args:
            input_dir: Directory containing model files to enrich.
            output_dir: Directory to save enriched models.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - enriched_models: List of paths to enriched model files
            - error: Error information if not successful
        """
        if not self.validate_input(input_dir=input_dir, output_dir=output_dir):
            return {
                "success": False,
                "error": {"message": "Invalid input for directory enrichment"}
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
                    "enriched_models": []
                }
            
            # Process each file
            enriched_models = []
            failed_models = []
            
            for model_file in model_files:
                try:
                    # Read the model data
                    model_data = self.reader.read_model(model_file)
                    
                    # Enrich the model
                    result = self.enrich_model(model_data)
                    
                    if not result["success"]:
                        self.logger.warning(f"Failed to enrich {model_file.name}: {result.get('error', {}).get('message', 'Unknown error')}")
                        failed_models.append(str(model_file))
                        continue
                    
                    # Write the enriched model
                    enriched_model = result["enriched_model"]
                    output_file = out_dir / f"{model_file.stem}_enriched.json"
                    output_path = self.writer.write_model(enriched_model, output_file)
                    enriched_models.append(output_path)
                    
                    self.logger.info(f"Enriched {model_file.name} -> {output_path}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing {model_file}: {str(e)}")
                    failed_models.append(str(model_file))
            
            self.logger.info(f"Enriched {len(enriched_models)} models. Failed: {len(failed_models)}")
            
            result = {
                "success": len(failed_models) == 0,
                "enriched_models": [str(path) for path in enriched_models]
            }
            
            if failed_models:
                result["failed_models"] = failed_models
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error enriching directory: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Directory enrichment error: {str(e)}", "type": type(e).__name__}
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
            
            # Check for required fields in model data
            if 'name' not in model_data:
                self.logger.error("Model data must contain a 'name' field")
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


class MetadataEnricher(BaseEnricher):
    """
    Enricher for adding and standardizing metadata to models.
    
    Adds consistent metadata fields to model data.
    """
    
    def _enrich_model_impl(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add standardized metadata to a model.
        
        Args:
            model_data: Dictionary containing the model data.
            
        Returns:
            Dictionary containing enrichment results.
        """
        self.logger.info(f"Enriching model '{model_data.get('name', 'unknown')}'")
        
        # Create a copy of the model data to avoid modifying the original
        enriched_model = model_data.copy()
        
        # Ensure modelId exists
        if 'modelId' not in enriched_model:
            enriched_model['modelId'] = self._generate_model_id(enriched_model)
            self.logger.info(f"Generated modelId: {enriched_model['modelId']}")
        
        # Ensure description exists
        if 'description' not in enriched_model or not enriched_model['description']:
            enriched_model['description'] = f"Model {enriched_model['name']}"
            self.logger.info(f"Added default description for {enriched_model['name']}")
        
        # Ensure parameters field exists
        if 'parameters' not in enriched_model:
            enriched_model['parameters'] = {}
        
        # Ensure tags field exists and is a list
        if 'tags' not in enriched_model:
            enriched_model['tags'] = []
        elif not isinstance(enriched_model['tags'], list):
            enriched_model['tags'] = [str(enriched_model['tags'])]
        
        # Ensure metadata field exists
        if 'metadata' not in enriched_model:
            enriched_model['metadata'] = {}
        
        # Add standard metadata fields if they don't exist
        metadata = enriched_model['metadata']
        
        if 'processed_date' not in metadata:
            from datetime import datetime
            metadata['processed_date'] = datetime.now().isoformat()
        
        if 'is_enriched' not in metadata:
            metadata['is_enriched'] = True
            
        # Set default display name if not present
        if 'display_name' not in enriched_model:
            enriched_model['display_name'] = self._generate_display_name(enriched_model['name'])
        
        self.logger.info(f"Successfully enriched model '{enriched_model['name']}'")
        
        return {
            "success": True,
            "enriched_model": enriched_model
        }
    
    def _generate_model_id(self, model_data: Dict[str, Any]) -> str:
        """
        Generate a modelId from the model data.
        
        Args:
            model_data: Dictionary containing the model data.
            
        Returns:
            Generated modelId string.
        """
        # Use the name as the base for the modelId
        name = model_data.get('name', '')
        
        # Add a prefix based on the source if available
        source = model_data.get('metadata', {}).get('source', '').lower()
        
        if source:
            return f"{source}-{name}"
        else:
            return f"model-{name}"
    
    def _generate_display_name(self, name: str) -> str:
        """
        Generate a human-readable display name from the model name.
        
        Args:
            name: Model name.
            
        Returns:
            Human-readable display name.
        """
        # Replace hyphens and underscores with spaces
        display_name = name.replace('-', ' ').replace('_', ' ')
        
        # Title case
        display_name = ' '.join(word.capitalize() for word in display_name.split())
        
        return display_name


class HuggingFaceEnricher(BaseEnricher):
    """
    Enricher for adding Hugging Face information to models.
    
    Fetches additional metadata from the Hugging Face API.
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the HuggingFace enricher.
        
        Args:
            api_key: Hugging Face API key. If None, tries to use HF_API_KEY environment variable.
            **kwargs: Additional arguments to pass to the parent constructor.
        """
        super().__init__(**kwargs)
        self.api_key = api_key
        
        # HF API base URL
        self.api_base_url = "https://huggingface.co/api"
    
    def _enrich_model_impl(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a model with Hugging Face information.
        
        Args:
            model_data: Dictionary containing the model data.
            
        Returns:
            Dictionary containing enrichment results.
        """
        model_name = model_data.get('name', '')
        self.logger.info(f"Enriching model '{model_name}' with Hugging Face data")
        
        # Create a copy of the model data to avoid modifying the original
        enriched_model = model_data.copy()
        
        # Try to find a matching model on Hugging Face
        hf_model = self._find_hf_model(model_name)
        
        if not hf_model:
            self.logger.warning(f"No matching Hugging Face model found for '{model_name}'")
            
            # Still return success but without HF enrichment
            return {
                "success": True,
                "enriched_model": enriched_model
            }
        
        # Add Hugging Face information to the model
        if 'metadata' not in enriched_model:
            enriched_model['metadata'] = {}
            
        metadata = enriched_model['metadata']
        
        # Add HF metadata
        metadata['huggingface'] = {
            'id': hf_model.get('id', ''),
            'author': hf_model.get('author', ''),
            'downloads': hf_model.get('downloads', 0),
            'likes': hf_model.get('likes', 0),
            'url': f"https://huggingface.co/{hf_model.get('id', '')}"
        }
        
        # Update description if HF has a better one and current is default/empty
        if (hf_model.get('description') and 
            (not enriched_model.get('description') or 
             enriched_model.get('description') == f"Model {model_name}")):
            enriched_model['description'] = hf_model.get('description')
            self.logger.info(f"Updated description from Hugging Face for '{model_name}'")
        
        # Add tags from HF if they exist
        if 'tags' in hf_model and isinstance(hf_model['tags'], list):
            existing_tags = set(enriched_model.get('tags', []))
            hf_tags = set(hf_model['tags'])
            
            # Add new tags from HF
            new_tags = hf_tags - existing_tags
            enriched_model['tags'] = list(existing_tags.union(new_tags))
            
            if new_tags:
                self.logger.info(f"Added {len(new_tags)} tags from Hugging Face: {', '.join(new_tags)}")
        
        # Add reference link if not present
        if 'referenceLink' not in enriched_model and 'id' in hf_model:
            enriched_model['referenceLink'] = f"https://huggingface.co/{hf_model['id']}"
        
        self.logger.info(f"Successfully enriched '{model_name}' with Hugging Face data")
        
        return {
            "success": True,
            "enriched_model": enriched_model
        }
    
    def _find_hf_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a matching model on Hugging Face.
        
        Args:
            model_name: Name of the model to find.
            
        Returns:
            Dictionary with Hugging Face model data, or None if not found.
        """
        try:
            # Normalize model name for search
            search_term = model_name.lower().replace('_', '-')
            
            # Prepare headers
            headers = {}
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"
            
            # Search for models
            url = f"{self.api_base_url}/models?search={search_term}"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                self.logger.warning(f"Hugging Face API request failed: {response.status_code} - {response.text}")
                return None
            
            models = response.json()
            
            if not models:
                return None
            
            # Try to find an exact match first
            for model in models:
                model_id = model.get('id', '').lower()
                if model_id == search_term or model_id.endswith(f"/{search_term}"):
                    return model
            
            # If no exact match, return the first result
            return models[0]
            
        except Exception as e:
            self.logger.error(f"Error searching Hugging Face API: {str(e)}")
            return None
