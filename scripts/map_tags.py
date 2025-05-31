#!/usr/bin/env python
"""
CLI script for mapping tags to models.

This script provides a command-line interface for mapping tag names
to tag IDs for model data.
"""

import argparse
import sys
from pathlib import Path

# Add the parent directory to the path so we can import pipeline modules
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from pipeline.config import get_config
from pipeline.factory import PipelineFactory
from pipeline.logger import get_logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Map tags to model data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Input/Output directories
    parser.add_argument(
        "--input-dir", 
        type=str,
        help="Directory containing enriched model data files"
    )
    parser.add_argument(
        "--output-dir", 
        type=str,
        help="Directory to save tagged model data"
    )
    
    # Tag mapping options
    parser.add_argument(
        "--tag-mapper-type",
        choices=["simple", "fallback"],
        default="simple",
        help="Type of tag mapper to use"
    )
    parser.add_argument(
        "--tag-map-file",
        type=str,
        help="Path to tag mapping file"
    )
    parser.add_argument(
        "--auto-create",
        action="store_true",
        help="Automatically create tags that don't exist in the mapping"
    )
    
    # General options
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the tag mapping script."""
    args = parse_args()
    
    # Configure logging
    # Note: The PipelineLogger doesn't take a level parameter in get_logger
    # We'll use the default log level from config
    logger = get_logger("TagMapperCLI")
    logger.info("Starting tag mapping")
    
    # Get configuration
    config = get_config()
    
    # Determine input/output directories and tag map file
    input_dir = args.input_dir or str(config.enriched_data_dir)
    output_dir = args.output_dir or str(config.processed_data_dir)
    tag_map_file = args.tag_map_file or str(config.tag_map_file)
    
    # Create tag mapper with additional options
    factory = PipelineFactory(logger=logger)
    tag_mapper_kwargs = {
        "logger": logger
    }
    tag_mapper = factory.create_tag_mapper(args.tag_mapper_type, **tag_mapper_kwargs)
    
    logger.info(f"Mapping tags for models in {input_dir} and saving to {output_dir}")
    logger.info(f"Using tag map file: {tag_map_file}")
    
    # Run tag mapping
    result = tag_mapper.map_directory(input_dir, output_dir, tag_map_file)
    
    # Check result
    if result["success"]:
        logger.info(f"Tag mapping completed successfully")
        if "mapped_models" in result:
            logger.info(f"Mapped tags for {len(result['mapped_models'])} models")
            for model_path in result.get("mapped_models", []):
                logger.info(f"  - {model_path}")
        exit_code = 0
    else:
        error = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"Tag mapping failed: {error}")
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
