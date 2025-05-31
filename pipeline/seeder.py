"""
Seeder component for the AI Model Seeding Pipeline.

This module provides implementations of the ISeeder interface
for seeding models to the backend API.
"""

import json
import time
from pathlib import Path
import requests
from typing import Any, Dict, List, Optional, Union

from pipeline.base import BaseComponent, BaseModelReader
from pipeline.interfaces import ILogger, IModelReader, ISeeder
from pipeline.logger import get_logger


class BaseSeeder(BaseComponent, ISeeder):
    """
    Base implementation of the ISeeder interface.
    
    Provides common functionality for all seeders.
    """
    
    def __init__(self, logger: Optional[ILogger] = None, reader: Optional[IModelReader] = None):
        """
        Initialize the seeder.
        
        Args:
            logger: Logger for logging events. If None, a default logger is used.
            reader: Reader for loading models. If None, a default reader is used.
        """
        super().__init__(logger or get_logger("Seeder"))
        self.reader = reader or BaseModelReader(self.logger)
    
    def seed_model(self, model_data: Dict[str, Any], api_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Seed a single model to the API.
        
        Args:
            model_data: Dictionary containing the API-ready model data.
            api_url: URL of the API endpoint.
            api_key: Optional API key for authentication.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - response: API response
            - error: Error information if not successful
        """
        if not self.validate_input(model_data=model_data, api_url=api_url):
            return {
                "success": False,
                "error": {"message": "Invalid input for seeding"}
            }
        
        try:
            return self._seed_model_impl(model_data, api_url, api_key)
        except Exception as e:
            self.logger.error(f"Error seeding model: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Seeding error: {str(e)}", "type": type(e).__name__}
            }
    
    def _seed_model_impl(self, model_data: Dict[str, Any], api_url: str, 
                        api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Implementation of model seeding logic.
        
        This should be overridden by subclasses.
        
        Args:
            model_data: Dictionary containing the API-ready model data.
            api_url: URL of the API endpoint.
            api_key: Optional API key for authentication.
            
        Returns:
            Dictionary containing seeding results.
            
        Raises:
            NotImplementedError: If not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses must implement _seed_model_impl")
    
    def seed_directory(self, input_dir: Union[str, Path], api_url: str, 
                      api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Seed all models in a directory to the API.
        
        Args:
            input_dir: Directory containing API-ready model files.
            api_url: URL of the API endpoint.
            api_key: Optional API key for authentication.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - seeded_models: List of successfully seeded models
            - failed_models: List of models that failed to seed
            - error: Error information if not successful
        """
        if not self.validate_input(input_dir=input_dir, api_url=api_url):
            return {
                "success": False,
                "error": {"message": "Invalid input for directory seeding"}
            }
        
        try:
            in_dir = Path(input_dir)
            if not in_dir.exists() or not in_dir.is_dir():
                return {
                    "success": False,
                    "error": {"message": f"Input directory not found: {in_dir}"}
                }
            
            # Find all JSON files in the input directory
            model_files = list(in_dir.glob("*.json"))
            
            if not model_files:
                self.logger.warning(f"No model files found in {in_dir}")
                return {
                    "success": True,
                    "seeded_models": []
                }
            
            # Process each file
            seeded_models = []
            failed_models = []
            
            for model_file in model_files:
                try:
                    # Read the model data
                    model_data = self.reader.read_model(model_file)
                    
                    # Seed the model
                    result = self.seed_model(model_data, api_url, api_key)
                    
                    if result["success"]:
                        seeded_models.append({
                            "file": str(model_file),
                            "modelId": model_data.get("modelId", "unknown"),
                            "name": model_data.get("name", "unknown"),
                            "response": result.get("response", {})
                        })
                        self.logger.info(f"Successfully seeded {model_file.name}")
                    else:
                        error_msg = result.get("error", {}).get("message", "Unknown error")
                        failed_models.append({
                            "file": str(model_file),
                            "modelId": model_data.get("modelId", "unknown"),
                            "name": model_data.get("name", "unknown"),
                            "error": error_msg
                        })
                        self.logger.warning(f"Failed to seed {model_file.name}: {error_msg}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing {model_file}: {str(e)}")
                    failed_models.append({
                        "file": str(model_file),
                        "error": str(e)
                    })
            
            self.logger.info(f"Seeded {len(seeded_models)} models. Failed: {len(failed_models)}")
            
            result = {
                "success": len(failed_models) == 0,
                "seeded_models": seeded_models
            }
            
            if failed_models:
                result["failed_models"] = failed_models
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error seeding directory: {str(e)}")
            return {
                "success": False,
                "error": {"message": f"Directory seeding error: {str(e)}", "type": type(e).__name__}
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
        
        # Validate api_url if provided
        if 'api_url' in kwargs:
            api_url = kwargs['api_url']
            if not api_url:
                self.logger.error("API URL is required")
                return False
        
        # Validate input_dir if provided
        if 'input_dir' in kwargs:
            input_dir = kwargs['input_dir']
            if not input_dir:
                self.logger.error("Input directory is required")
                return False
        
        return True


class RestApiSeeder(BaseSeeder):
    """
    Seeder implementation for REST APIs.
    
    Seeds models to a REST API endpoint.
    """
    
    def __init__(self, timeout: int = 30, retries: int = 3, retry_delay: int = 2, **kwargs):
        """
        Initialize the REST API seeder.
        
        Args:
            timeout: Timeout for API requests in seconds.
            retries: Number of retries for failed requests.
            retry_delay: Delay between retries in seconds.
            **kwargs: Additional arguments to pass to the parent constructor.
        """
        super().__init__(**kwargs)
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
    
    def _seed_model_impl(self, model_data: Dict[str, Any], api_url: str, 
                        api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Seed a model to a REST API.
        
        Args:
            model_data: Dictionary containing the API-ready model data.
            api_url: URL of the API endpoint.
            api_key: Optional API key for authentication.
            
        Returns:
            Dictionary containing seeding results.
        """
        model_id = model_data.get("modelId", "unknown")
        model_name = model_data.get("name", "unknown")
        
        self.logger.info(f"Seeding model '{model_name}' (ID: {model_id}) to {api_url}")
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json"
        }
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # Prepare the request
        attempt = 0
        while attempt < self.retries:
            attempt += 1
            
            try:
                response = requests.post(
                    api_url,
                    json=model_data,
                    headers=headers,
                    timeout=self.timeout
                )
                
                # Check if the request was successful
                if response.status_code in (200, 201, 202):
                    try:
                        response_data = response.json()
                    except:
                        response_data = {"message": "Success (no JSON response)"}
                    
                    self.logger.info(f"Successfully seeded model '{model_name}' (ID: {model_id})")
                    
                    return {
                        "success": True,
                        "response": response_data,
                        "status_code": response.status_code
                    }
                else:
                    # Handle error responses
                    try:
                        error_data = response.json()
                    except:
                        error_data = {"message": response.text or "Unknown error"}
                    
                    error_message = f"API request failed with status {response.status_code}: {error_data.get('message', 'Unknown error')}"
                    
                    # Check if we should retry
                    if attempt < self.retries and response.status_code >= 500:
                        self.logger.warning(f"Retrying after server error (attempt {attempt}/{self.retries}): {error_message}")
                        time.sleep(self.retry_delay)
                        continue
                    
                    self.logger.error(f"Failed to seed model '{model_name}': {error_message}")
                    
                    return {
                        "success": False,
                        "error": {
                            "message": error_message,
                            "status_code": response.status_code,
                            "response": error_data
                        }
                    }
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.retries:
                    self.logger.warning(f"Request error (attempt {attempt}/{self.retries}): {str(e)}")
                    time.sleep(self.retry_delay)
                    continue
                
                self.logger.error(f"Request failed after {self.retries} attempts: {str(e)}")
                
                return {
                    "success": False,
                    "error": {
                        "message": f"Request error: {str(e)}",
                        "type": type(e).__name__
                    }
                }
        
        # This should never be reached, but just in case
        return {
            "success": False,
            "error": {
                "message": f"All {self.retries} attempts failed"
            }
        }


class MockSeeder(BaseSeeder):
    """
    Mock seeder for testing.
    
    Simulates seeding models to an API without making actual API calls.
    """
    
    def __init__(self, success_rate: float = 0.9, delay: float = 0.5, **kwargs):
        """
        Initialize the mock seeder.
        
        Args:
            success_rate: Probability of successful seeding (0.0 to 1.0).
            delay: Simulated delay in seconds.
            **kwargs: Additional arguments to pass to the parent constructor.
        """
        super().__init__(**kwargs)
        self.success_rate = max(0.0, min(1.0, success_rate))
        self.delay = delay
    
    def _seed_model_impl(self, model_data: Dict[str, Any], api_url: str, 
                        api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate seeding a model.
        
        Args:
            model_data: Dictionary containing the API-ready model data.
            api_url: URL of the API endpoint (ignored).
            api_key: Optional API key for authentication (ignored).
            
        Returns:
            Dictionary containing simulated seeding results.
        """
        model_id = model_data.get("modelId", "unknown")
        model_name = model_data.get("name", "unknown")
        
        self.logger.info(f"Mock seeding model '{model_name}' (ID: {model_id})")
        
        # Simulate API delay
        time.sleep(self.delay)
        
        # Determine success based on success rate
        import random
        success = random.random() < self.success_rate
        
        if success:
            self.logger.info(f"Successfully seeded model '{model_name}' (mock)")
            
            return {
                "success": True,
                "response": {
                    "id": model_id,
                    "name": model_name,
                    "message": "Model created successfully (mock)",
                    "timestamp": time.time()
                },
                "status_code": 201
            }
        else:
            error_message = "Simulated API error"
            self.logger.error(f"Failed to seed model '{model_name}': {error_message} (mock)")
            
            return {
                "success": False,
                "error": {
                    "message": error_message,
                    "status_code": 400,
                    "response": {
                        "error": "Bad Request",
                        "message": "Simulated API error (mock)"
                    }
                }
            }
