"""
Pipeline orchestrator for the AI Model Seeding Pipeline.

This module provides the orchestrator that coordinates all pipeline components
and manages the flow of data between them.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from pipeline.base import BaseComponent
from pipeline.config import get_config
from pipeline.interfaces import (
    IArchiver,
    IComponent,
    IEnricher,
    IExtractor,
    ILogger,
    IModelMapper,
    IPipeline,
    ISeeder,
    ITagMapper
)
from pipeline.logger import get_logger


class Pipeline(IPipeline):
    """
    Pipeline orchestrator for the AI Model Seeding Pipeline.
    
    Coordinates the execution of all pipeline phases and manages
    the flow of data between components.
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        """
        Initialize the pipeline orchestrator.
        
        Args:
            logger: Logger for logging events. If None, a default logger is used.
        """
        self.logger = logger or get_logger("Pipeline")
        self.config = get_config()
        
        # Component registry
        self.components = {}
        
        # Pipeline phase results
        self.results = {}
    
    def register_component(self, component_type: str, component: IComponent) -> None:
        """
        Register a component with the pipeline.
        
        Args:
            component_type: Type of the component (e.g., 'extractor', 'enricher').
            component: Component instance.
        """
        self.components[component_type] = component
        self.logger.info(f"Registered component '{component_type}'")
    
    def get_component(self, component_type: str) -> Optional[IComponent]:
        """
        Get a registered component.
        
        Args:
            component_type: Type of the component to get.
            
        Returns:
            The component instance or None if not registered.
        """
        if component_type not in self.components:
            self.logger.warning(f"Component '{component_type}' not registered")
            return None
        
        return self.components[component_type]
    
    def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete pipeline.
        
        Args:
            config: Pipeline configuration.
            
        Returns:
            Dictionary containing the pipeline results.
        """
        self.logger.info("Starting pipeline execution")
        self.results = {}
        
        # Ensure required components are registered
        required_components = ['extractor', 'enricher', 'tag_mapper', 'model_mapper', 'seeder', 'archiver']
        missing_components = [c for c in required_components if c not in self.components]
        
        if missing_components:
            error_msg = f"Missing required components: {', '.join(missing_components)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": {"message": error_msg}
            }
        
        try:
            # Extract phase
            extract_result = self.run_phase('extract', {
                'source_config': config.get('source_config', {}),
                'output_dir': config.get('raw_data_dir', self.config.raw_data_dir)
            })
            
            if not extract_result["success"]:
                return self._pipeline_error("Extraction phase failed", extract_result)
            
            # Enrich phase
            enrich_result = self.run_phase('enrich', {
                'input_dir': config.get('raw_data_dir', self.config.raw_data_dir),
                'output_dir': config.get('enriched_data_dir', self.config.enriched_data_dir)
            })
            
            if not enrich_result["success"]:
                return self._pipeline_error("Enrichment phase failed", enrich_result)
            
            # Tag mapping phase
            tag_map_result = self.run_phase('map_tags', {
                'input_dir': config.get('enriched_data_dir', self.config.enriched_data_dir),
                'output_dir': config.get('processed_data_dir', self.config.processed_data_dir),
                'tag_map_file': config.get('tag_map_file', self.config.tag_map_file)
            })
            
            if not tag_map_result["success"]:
                return self._pipeline_error("Tag mapping phase failed", tag_map_result)
            
            # Model mapping phase
            model_map_result = self.run_phase('map_models', {
                'input_dir': config.get('processed_data_dir', self.config.processed_data_dir),
                'output_dir': config.get('mapped_data_dir', self.config.mapped_data_dir)
            })
            
            if not model_map_result["success"]:
                return self._pipeline_error("Model mapping phase failed", model_map_result)
            
            # Seeding phase
            seed_result = self.run_phase('seed', {
                'input_dir': config.get('mapped_data_dir', self.config.mapped_data_dir),
                'api_url': config.get('api_url', self.config.api_url),
                'api_key': config.get('api_key', self.config.api_key)
            })
            
            if not seed_result["success"]:
                return self._pipeline_error("Seeding phase failed", seed_result)
            
            # Archiving phase
            archive_result = self.run_phase('archive', {
                'input_dir': config.get('mapped_data_dir', self.config.mapped_data_dir),
                'archive_dir': config.get('archive_dir', self.config.archive_dir)
            })
            
            if not archive_result["success"]:
                return self._pipeline_error("Archiving phase failed", archive_result)
            
            # Pipeline completed successfully
            self.logger.info("Pipeline execution completed successfully")
            
            return {
                "success": True,
                "results": self.results
            }
            
        except Exception as e:
            error_msg = f"Pipeline execution failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": {"message": error_msg, "type": type(e).__name__}
            }
    
    def run_phase(self, phase_name: str, input_data: Any) -> Dict[str, Any]:
        """
        Run a specific phase of the pipeline.
        
        Args:
            phase_name: Name of the phase to run.
            input_data: Input data for the phase.
            
        Returns:
            Dictionary containing the phase results.
        """
        self.logger.info(f"Starting pipeline phase: {phase_name}")
        
        # Map phase name to component type and method
        phase_map = {
            'extract': ('extractor', self._run_extract),
            'enrich': ('enricher', self._run_enrich),
            'map_tags': ('tag_mapper', self._run_tag_mapping),
            'map_models': ('model_mapper', self._run_model_mapping),
            'seed': ('seeder', self._run_seeding),
            'archive': ('archiver', self._run_archiving)
        }
        
        if phase_name not in phase_map:
            error_msg = f"Unknown pipeline phase: {phase_name}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": {"message": error_msg}
            }
        
        component_type, method = phase_map[phase_name]
        component = self.get_component(component_type)
        
        if not component:
            error_msg = f"Component '{component_type}' not registered for phase '{phase_name}'"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": {"message": error_msg}
            }
        
        try:
            # Execute the phase method
            result = method(component, input_data)
            
            # Store the result
            self.results[phase_name] = result
            
            self.logger.info(f"Completed pipeline phase: {phase_name}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error in pipeline phase '{phase_name}': {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": {"message": error_msg, "type": type(e).__name__}
            }
    
    def _run_extract(self, component: IExtractor, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the extraction phase.
        
        Args:
            component: Extraction component.
            input_data: Input data for the phase.
            
        Returns:
            Dictionary containing the phase results.
        """
        self.logger.info("Running extraction phase")
        
        source_config = input_data.get('source_config', {})
        output_dir = input_data.get('output_dir')
        
        return component.extract_from_source(source_config, output_dir)
    
    def _run_enrich(self, component: IEnricher, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the enrichment phase.
        
        Args:
            component: Enrichment component.
            input_data: Input data for the phase.
            
        Returns:
            Dictionary containing the phase results.
        """
        self.logger.info("Running enrichment phase")
        
        input_dir = input_data.get('input_dir')
        output_dir = input_data.get('output_dir')
        
        return component.enrich_directory(input_dir, output_dir)
    
    def _run_tag_mapping(self, component: ITagMapper, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the tag mapping phase.
        
        Args:
            component: Tag mapping component.
            input_data: Input data for the phase.
            
        Returns:
            Dictionary containing the phase results.
        """
        self.logger.info("Running tag mapping phase")
        
        input_dir = input_data.get('input_dir')
        output_dir = input_data.get('output_dir')
        tag_map_file = input_data.get('tag_map_file')
        
        return component.map_directory(input_dir, output_dir, tag_map_file)
    
    def _run_model_mapping(self, component: IModelMapper, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the model mapping phase.
        
        Args:
            component: Model mapping component.
            input_data: Input data for the phase.
            
        Returns:
            Dictionary containing the phase results.
        """
        self.logger.info("Running model mapping phase")
        
        input_dir = input_data.get('input_dir')
        output_dir = input_data.get('output_dir')
        
        return component.map_directory(input_dir, output_dir)
    
    def _run_seeding(self, component: ISeeder, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the seeding phase.
        
        Args:
            component: Seeding component.
            input_data: Input data for the phase.
            
        Returns:
            Dictionary containing the phase results.
        """
        self.logger.info("Running seeding phase")
        
        input_dir = input_data.get('input_dir')
        api_url = input_data.get('api_url')
        api_key = input_data.get('api_key')
        
        return component.seed_directory(input_dir, api_url, api_key)
    
    def _run_archiving(self, component: IArchiver, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the archiving phase.
        
        Args:
            component: Archiving component.
            input_data: Input data for the phase.
            
        Returns:
            Dictionary containing the phase results.
        """
        self.logger.info("Running archiving phase")
        
        input_dir = input_data.get('input_dir')
        archive_dir = input_data.get('archive_dir')
        
        return component.archive_directory(input_dir, archive_dir)
    
    def _pipeline_error(self, message: str, phase_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a pipeline error response.
        
        Args:
            message: Error message.
            phase_result: Result from the failed phase.
            
        Returns:
            Pipeline error response.
        """
        error = phase_result.get("error", {"message": "Unknown error"})
        error_msg = f"{message}: {error.get('message', 'Unknown error')}"
        self.logger.error(error_msg)
        
        return {
            "success": False,
            "error": {
                "message": error_msg,
                "phase_result": phase_result
            },
            "results": self.results
        }
