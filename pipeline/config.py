"""
Configuration management for the AI Model Seeding Pipeline.

This module loads configuration from environment variables and provides
a centralized access point for all configuration settings.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from loguru import logger


class PipelineConfig:
    """
    Configuration manager for the AI Model Seeding Pipeline.
    
    Loads configuration from environment variables, with sensible defaults.
    All paths are converted to absolute paths for consistency.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            env_file: Path to the .env file to load. If None, looks for .env in the project root.
        """
        # Load environment variables from .env file
        self.project_root = Path(__file__).parent.parent.absolute()
        
        if env_file:
            env_path = Path(env_file)
        else:
            env_path = self.project_root / ".env"
            
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Loaded configuration from {env_path}")
        
        # Initialize configuration
        self._init_directories()
        self._init_logging()
        self._init_api_settings()
        self._init_extraction_settings()
        self._init_enrichment_settings()
        self._init_tag_mapping_settings()
        self._init_model_mapping_settings()
        self._init_seeding_settings()
        self._init_archiving_settings()
        self._init_component_defaults()
        
    def _init_directories(self):
        """Initialize directory configuration."""
        self.data_dir = self._get_abs_path(os.getenv("DATA_DIR", "./data"))
        self.raw_data_dir = self._get_abs_path(os.getenv("RAW_DATA_DIR", "./data/raw"))
        self.enriched_data_dir = self._get_abs_path(os.getenv("ENRICHED_DATA_DIR", "./data/enriched"))
        self.processed_data_dir = self._get_abs_path(os.getenv("PROCESSED_DATA_DIR", "./data/processed"))
        self.mapped_data_dir = self._get_abs_path(os.getenv("MAPPED_DATA_DIR", "./data/mapped"))
        self.archive_dir = self._get_abs_path(os.getenv("ARCHIVE_DIR", "./archive"))
        self.tags_dir = self._get_abs_path(os.getenv("TAGS_DIR", "./Tags"))
        
    def _init_logging(self):
        """Initialize logging configuration."""
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = self._get_abs_path(os.getenv("LOG_FILE", "./logs/pipeline.log"))
        self.console_log = self._parse_bool(os.getenv("CONSOLE_LOG", "true"))
        self.file_log = self._parse_bool(os.getenv("FILE_LOG", "true"))
        
    def _init_api_settings(self):
        """Initialize API configuration."""
        self.api_url = os.getenv("API_URL", "http://localhost:8000/api")
        self.api_key = os.getenv("API_KEY", "")
        self.api_timeout = int(os.getenv("API_TIMEOUT", "30"))
        self.api_retry_attempts = int(os.getenv("API_RETRY_ATTEMPTS", "3"))
        
    def _init_extraction_settings(self):
        """Initialize extraction configuration."""
        self.extract_batch_size = int(os.getenv("EXTRACT_BATCH_SIZE", "10"))
        self.extract_parallel = self._parse_bool(os.getenv("EXTRACT_PARALLEL", "false"))
        
    def _init_enrichment_settings(self):
        """Initialize enrichment configuration."""
        sources = os.getenv("ENRICHMENT_SOURCES", "huggingface,custom")
        self.enrichment_sources = [s.strip() for s in sources.split(",")]
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY", "")
        
    def _init_tag_mapping_settings(self):
        """Initialize tag mapping configuration."""
        self.tag_map_file = self._get_abs_path(os.getenv("TAG_MAP_FILE", "./Tags/created_tag_ids.json"))
        self.auto_create_tags = self._parse_bool(os.getenv("AUTO_CREATE_TAGS", "false"))
        
    def _init_model_mapping_settings(self):
        """Initialize model mapping configuration."""
        self.schema_validation = self._parse_bool(os.getenv("SCHEMA_VALIDATION", "true"))
        self.placeholder_url = os.getenv("PLACEHOLDER_URL", "https://example.com/placeholder")
        
    def _init_seeding_settings(self):
        """Initialize seeding configuration."""
        self.seed_batch_size = int(os.getenv("SEED_BATCH_SIZE", "5"))
        self.seed_parallel = self._parse_bool(os.getenv("SEED_PARALLEL", "false"))
        self.seed_delay = float(os.getenv("SEED_DELAY", "1"))
        
    def _init_archiving_settings(self):
        """Initialize archiving configuration."""
        self.archive_format = os.getenv("ARCHIVE_FORMAT", "original")
        self.include_timestamp = self._parse_bool(os.getenv("INCLUDE_TIMESTAMP", "true"))
        self.auto_cleanup = self._parse_bool(os.getenv("AUTO_CLEANUP", "false"))
        
    def _init_component_defaults(self):
        """Initialize default component type settings."""
        self.default_extractor_type = os.getenv("DEFAULT_EXTRACTOR_TYPE", "ollama")
        self.default_enricher_type = os.getenv("DEFAULT_ENRICHER_TYPE", "metadata")
        self.default_tag_mapper_type = os.getenv("DEFAULT_TAG_MAPPER_TYPE", "simple")
        self.default_model_mapper_type = os.getenv("DEFAULT_MODEL_MAPPER_TYPE", "standard")
        self.default_seeder_type = os.getenv("DEFAULT_SEEDER_TYPE", "api")
        self.default_archiver_type = os.getenv("DEFAULT_ARCHIVER_TYPE", "metadata")
        
    def _get_abs_path(self, path: str) -> Path:
        """
        Convert a relative path to an absolute path.
        
        Args:
            path: Relative or absolute path.
            
        Returns:
            Absolute path as a Path object.
        """
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return (self.project_root / path_obj).resolve()
    
    def _parse_bool(self, value: str) -> bool:
        """
        Parse a string as a boolean.
        
        Args:
            value: String representation of a boolean.
            
        Returns:
            Boolean value.
        """
        return value.lower() in ("true", "t", "yes", "y", "1")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.
        
        Returns:
            Dictionary of configuration values.
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


# Create a singleton instance of the configuration
config = PipelineConfig()


def get_config() -> PipelineConfig:
    """
    Get the configuration instance.
    
    Returns:
        The singleton configuration instance.
    """
    return config


if __name__ == "__main__":
    # If run directly, print the configuration
    import json
    from pathlib import Path
    
    cfg = get_config()
    config_dict = cfg.to_dict()
    
    # Convert Path objects to strings for JSON serialization
    for key, value in config_dict.items():
        if isinstance(value, Path):
            config_dict[key] = str(value)
    
    print(json.dumps(config_dict, indent=2))
