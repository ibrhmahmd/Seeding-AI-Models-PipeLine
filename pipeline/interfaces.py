"""
Core interfaces for the AI Model Seeding Pipeline.

This module defines the abstract base classes and interfaces that form the
foundation of the pipeline architecture. These interfaces establish the
contracts that concrete implementations must fulfill.
"""

import abc
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ILogger(abc.ABC):
    """Interface for logging functionality."""
    
    @abc.abstractmethod
    def info(self, message: str) -> None:
        """Log an informational message."""
        pass
    
    @abc.abstractmethod
    def warning(self, message: str) -> None:
        """Log a warning message."""
        pass
    
    @abc.abstractmethod
    def error(self, message: str) -> None:
        """Log an error message."""
        pass
    
    @abc.abstractmethod
    def debug(self, message: str) -> None:
        """Log a debug message."""
        pass


class IModelReader(abc.ABC):
    """Interface for reading model data from files."""
    
    @abc.abstractmethod
    def read_model(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read model data from a file.
        
        Args:
            file_path: Path to the model file.
            
        Returns:
            Dictionary containing the model data.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a valid model file.
        """
        pass
    
    @abc.abstractmethod
    def list_models(self, directory: Union[str, Path]) -> List[Path]:
        """
        List available model files in a directory.
        
        Args:
            directory: Directory to search for model files.
            
        Returns:
            List of paths to model files.
        """
        pass


class IModelWriter(abc.ABC):
    """Interface for writing model data to files."""
    
    @abc.abstractmethod
    def write_model(self, model_data: Dict[str, Any], file_path: Union[str, Path]) -> Path:
        """
        Write model data to a file.
        
        Args:
            model_data: Dictionary containing the model data.
            file_path: Path where the model file should be written.
            
        Returns:
            Path to the written file.
            
        Raises:
            IOError: If the file cannot be written.
        """
        pass


class IComponent(abc.ABC):
    """Base interface for all pipeline components."""
    
    @abc.abstractmethod
    def process(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Process input data and return results.
        
        The signature is intentionally generic to allow specialized components
        to define their specific parameter requirements.
        
        Returns:
            Dictionary containing at minimum:
            - success: Boolean indicating success or failure
            - result: The processing result if successful
            - error: Error information if not successful
        """
        pass
    
    @abc.abstractmethod
    def validate_input(self, *args: Any, **kwargs: Any) -> bool:
        """
        Validate that the input meets the component's requirements.
        
        Returns:
            True if input is valid, False otherwise.
        """
        pass


class IExtractor(IComponent):
    """Interface for model extraction functionality."""
    
    @abc.abstractmethod
    def extract_from_source(self, source_config: Dict[str, Any], output_dir: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract models from a source and save to the output directory.
        
        Args:
            source_config: Configuration for the source.
            output_dir: Directory to save extracted models.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - extracted_models: List of paths to extracted model files
            - error: Error information if not successful
        """
        pass
    
    @abc.abstractmethod
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
        pass


class IEnricher(IComponent):
    """Interface for model enrichment functionality."""
    
    @abc.abstractmethod
    def enrich_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a single model with additional metadata.
        
        Args:
            model_data: Dictionary containing the model data.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - enriched_model: Dictionary with enriched model data
            - error: Error information if not successful
        """
        pass
    
    @abc.abstractmethod
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
        pass


class ITagMapper(IComponent):
    """Interface for mapping tags to models."""
    
    @abc.abstractmethod
    def map_tags(self, model_data: Dict[str, Any], tag_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map tags to a model.
        
        Args:
            model_data: Dictionary containing the model data.
            tag_map: Dictionary mapping tag names to tag IDs.
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success or failure
            - tagged_model: Dictionary with tagged model data
            - error: Error information if not successful
        """
        pass
    
    @abc.abstractmethod
    def map_directory(self, input_dir: Union[str, Path], output_dir: Union[str, Path], tag_map_file: Union[str, Path]) -> Dict[str, Any]:
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
        pass


class IModelMapper(IComponent):
    """Interface for mapping models to API schema."""
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
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
        pass


class ISeeder(IComponent):
    """Interface for seeding models to the API."""
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
    def seed_directory(self, input_dir: Union[str, Path], api_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
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
        pass


class IArchiver(IComponent):
    """Interface for archiving processed files."""
    
    @abc.abstractmethod
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
        pass
    
    @abc.abstractmethod
    def archive_directory(self, input_dir: Union[str, Path], archive_dir: Union[str, Path], pattern: Optional[str] = None) -> Dict[str, Any]:
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
        pass


class IPipeline(abc.ABC):
    """Interface for the pipeline orchestrator."""
    
    @abc.abstractmethod
    def register_component(self, component_type: str, component: IComponent) -> None:
        """
        Register a component with the pipeline.
        
        Args:
            component_type: Type of the component (e.g., 'extractor', 'enricher').
            component: Component instance.
        """
        pass
    
    @abc.abstractmethod
    def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the pipeline with the given configuration.
        
        Args:
            config: Pipeline configuration.
            
        Returns:
            Dictionary containing the pipeline results.
        """
        pass
    
    @abc.abstractmethod
    def run_phase(self, phase_name: str, input_data: Any) -> Dict[str, Any]:
        """
        Run a specific phase of the pipeline.
        
        Args:
            phase_name: Name of the phase to run.
            input_data: Input data for the phase.
            
        Returns:
            Dictionary containing the phase results.
        """
        pass
