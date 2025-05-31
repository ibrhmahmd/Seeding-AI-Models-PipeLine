"""
Factory for creating pipeline components and assembling the pipeline.

This module provides a factory for creating instances of pipeline
components and assembling them into a complete pipeline.
"""

from typing import Any, Dict, Optional, Type

from pipeline.archiver import MetadataArchiver, OrganizedArchiver, SimpleArchiver
from pipeline.config import get_config
from pipeline.enricher import HuggingFaceEnricher, MetadataEnricher
from pipeline.extractor import JsonFileExtractor, OllamaExtractor
from pipeline.interfaces import (
    IArchiver,
    IEnricher,
    IExtractor,
    ILogger,
    IModelMapper,
    IPipeline,
    ISeeder,
    ITagMapper
)
from pipeline.logger import PipelineLogger, get_logger
from pipeline.model_mapper import StandardModelMapper
from pipeline.pipeline import Pipeline
from pipeline.seeder import MockSeeder, RestApiSeeder
from pipeline.tag_mapper import FallbackTagMapper, SimpleTagMapper


class PipelineFactory:
    """
    Factory for creating pipeline components and assembling the pipeline.
    """
    
    def __init__(self, logger: Optional[ILogger] = None):
        """
        Initialize the pipeline factory.
        
        Args:
            logger: Logger for logging events. If None, a default logger is used.
        """
        self.logger = logger or get_logger("PipelineFactory")
        self.config = get_config()
    
    def create_extractor(self, extractor_type: str = None, **kwargs) -> IExtractor:
        """
        Create an extractor component.
        
        Args:
            extractor_type: Type of extractor to create. If None, uses the configured default.
            **kwargs: Additional arguments to pass to the extractor constructor.
            
        Returns:
            An extractor instance.
            
        Raises:
            ValueError: If the specified extractor type is not recognized.
        """
        if not extractor_type:
            extractor_type = self.config.default_extractor_type
        
        self.logger.debug(f"Creating extractor of type '{extractor_type}'")
        
        if extractor_type.lower() == "ollama":
            return OllamaExtractor(**kwargs)
        elif extractor_type.lower() == "json":
            return JsonFileExtractor(**kwargs)
        else:
            raise ValueError(f"Unknown extractor type: {extractor_type}")
    
    def create_enricher(self, enricher_type: str = None, **kwargs) -> IEnricher:
        """
        Create an enricher component.
        
        Args:
            enricher_type: Type of enricher to create. If None, uses the configured default.
            **kwargs: Additional arguments to pass to the enricher constructor.
            
        Returns:
            An enricher instance.
            
        Raises:
            ValueError: If the specified enricher type is not recognized.
        """
        if not enricher_type:
            enricher_type = self.config.default_enricher_type
        
        self.logger.debug(f"Creating enricher of type '{enricher_type}'")
        
        if enricher_type.lower() == "metadata":
            return MetadataEnricher(**kwargs)
        elif enricher_type.lower() == "huggingface":
            return HuggingFaceEnricher(**kwargs)
        else:
            raise ValueError(f"Unknown enricher type: {enricher_type}")
    
    def create_tag_mapper(self, tag_mapper_type: str = None, **kwargs) -> ITagMapper:
        """
        Create a tag mapper component.
        
        Args:
            tag_mapper_type: Type of tag mapper to create. If None, uses the configured default.
            **kwargs: Additional arguments to pass to the tag mapper constructor.
            
        Returns:
            A tag mapper instance.
            
        Raises:
            ValueError: If the specified tag mapper type is not recognized.
        """
        if not tag_mapper_type:
            tag_mapper_type = self.config.default_tag_mapper_type
        
        self.logger.debug(f"Creating tag mapper of type '{tag_mapper_type}'")
        
        if tag_mapper_type.lower() == "simple":
            return SimpleTagMapper(**kwargs)
        elif tag_mapper_type.lower() == "fallback":
            return FallbackTagMapper(**kwargs)
        else:
            raise ValueError(f"Unknown tag mapper type: {tag_mapper_type}")
    
    def create_model_mapper(self, model_mapper_type: str = None, **kwargs) -> IModelMapper:
        """
        Create a model mapper component.
        
        Args:
            model_mapper_type: Type of model mapper to create. If None, uses the configured default.
            **kwargs: Additional arguments to pass to the model mapper constructor.
            
        Returns:
            A model mapper instance.
            
        Raises:
            ValueError: If the specified model mapper type is not recognized.
        """
        if not model_mapper_type:
            model_mapper_type = self.config.default_model_mapper_type
        
        self.logger.debug(f"Creating model mapper of type '{model_mapper_type}'")
        
        if model_mapper_type.lower() == "standard":
            return StandardModelMapper(**kwargs)
        else:
            raise ValueError(f"Unknown model mapper type: {model_mapper_type}")
    
    def create_seeder(self, seeder_type: str = None, **kwargs) -> ISeeder:
        """
        Create a seeder component.
        
        Args:
            seeder_type: Type of seeder to create. If None, uses the configured default.
            **kwargs: Additional arguments to pass to the seeder constructor.
            
        Returns:
            A seeder instance.
            
        Raises:
            ValueError: If the specified seeder type is not recognized.
        """
        if not seeder_type:
            seeder_type = self.config.default_seeder_type
        
        self.logger.debug(f"Creating seeder of type '{seeder_type}'")
        
        if seeder_type.lower() == "api":
            return RestApiSeeder(**kwargs)
        elif seeder_type.lower() == "mock":
            return MockSeeder(**kwargs)
        else:
            raise ValueError(f"Unknown seeder type: {seeder_type}")
    
    def create_archiver(self, archiver_type: str = None, **kwargs) -> IArchiver:
        """
        Create an archiver component.
        
        Args:
            archiver_type: Type of archiver to create. If None, uses the configured default.
            **kwargs: Additional arguments to pass to the archiver constructor.
            
        Returns:
            An archiver instance.
            
        Raises:
            ValueError: If the specified archiver type is not recognized.
        """
        if not archiver_type:
            archiver_type = self.config.default_archiver_type
        
        self.logger.debug(f"Creating archiver of type '{archiver_type}'")
        
        if archiver_type.lower() == "simple":
            return SimpleArchiver(**kwargs)
        elif archiver_type.lower() == "organized":
            return OrganizedArchiver(**kwargs)
        elif archiver_type.lower() == "metadata":
            return MetadataArchiver(**kwargs)
        else:
            raise ValueError(f"Unknown archiver type: {archiver_type}")
    
    def create_pipeline(self, pipeline_config: Dict[str, Any] = None) -> IPipeline:
        """
        Create and assemble a complete pipeline.
        
        Args:
            pipeline_config: Configuration for the pipeline. If None, uses the default configuration.
            
        Returns:
            A fully assembled pipeline ready to run.
        """
        self.logger.info("Creating and assembling pipeline")
        
        # Use default config if none provided
        config = pipeline_config or {}
        
        # Create pipeline instance
        pipeline = Pipeline(logger=self.logger)
        
        # Create and register components
        extractor = self.create_extractor(
            extractor_type=config.get("extractor_type"),
            logger=self.logger
        )
        pipeline.register_component("extractor", extractor)
        
        enricher = self.create_enricher(
            enricher_type=config.get("enricher_type"),
            logger=self.logger
        )
        pipeline.register_component("enricher", enricher)
        
        tag_mapper = self.create_tag_mapper(
            tag_mapper_type=config.get("tag_mapper_type"),
            logger=self.logger
        )
        pipeline.register_component("tag_mapper", tag_mapper)
        
        model_mapper = self.create_model_mapper(
            model_mapper_type=config.get("model_mapper_type"),
            logger=self.logger
        )
        pipeline.register_component("model_mapper", model_mapper)
        
        seeder = self.create_seeder(
            seeder_type=config.get("seeder_type"),
            logger=self.logger
        )
        pipeline.register_component("seeder", seeder)
        
        archiver = self.create_archiver(
            archiver_type=config.get("archiver_type"),
            logger=self.logger
        )
        pipeline.register_component("archiver", archiver)
        
        self.logger.info("Pipeline assembly complete")
        
        return pipeline
