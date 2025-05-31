"""
AI Model Seeding Pipeline.

This package provides a modular, extensible pipeline for extracting, 
enriching, mapping, and seeding AI model data to an API, following
SOLID principles.
"""

__version__ = "0.1.0"

# Import commonly used components for easier access
from pipeline.config import get_config
from pipeline.logger import get_logger
from pipeline.interfaces import (
    IComponent,
    IExtractor,
    IEnricher,
    ITagMapper,
    IModelMapper,
    ISeeder,
    IArchiver,
    IPipeline
)
from pipeline.base import (
    BaseLogger,
    BaseModelReader,
    BaseModelWriter,
    BaseComponent,
    ensure_directory
)
