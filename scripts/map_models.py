#!/usr/bin/env python
"""
CLI script for mapping models to the API schema.

This script provides a command-line interface for mapping tagged model data
to the format expected by the API.
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
        description="Map models to API schema",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Input/Output directories
    parser.add_argument(
        "--input-dir", 
        type=str,
        help="Directory containing tagged model data files"
    )
    parser.add_argument(
        "--output-dir", 
        type=str,
        help="Directory to save API-ready model data"
    )
    
    # Model mapping options
    parser.add_argument(
        "--model-mapper-type",
        choices=["standard"],
        default="standard",
        help="Type of model mapper to use"
    )
    parser.add_argument(
        "--validate-schema",
        action="store_true",
        help="Validate models against API schema"
    )
    parser.add_argument(
        "--reference-url-prefix",
        type=str,
        help="Prefix for reference URLs in mapped models"
    )
    
    # General options
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the model mapping script."""
    args = parse_args()
    
    # Configure logging
    # Note: The PipelineLogger doesn't take a level parameter in get_logger
    # We'll use the default log level from config
    logger = get_logger("ModelMapperCLI")
    logger.info("Starting model mapping to API schema")
    
    # Get configuration
    config = get_config()
    
    # Determine input/output directories
    input_dir = args.input_dir or str(config.processed_data_dir)
    output_dir = args.output_dir or str(config.mapped_data_dir)
    
    # Create model mapper with additional options
    factory = PipelineFactory(logger=logger)
    model_mapper_kwargs = {
        "logger": logger,
        "validate_schema": args.validate_schema,
    }
    
    if args.reference_url_prefix:
        model_mapper_kwargs["reference_url_prefix"] = args.reference_url_prefix
    
    model_mapper = factory.create_model_mapper(args.model_mapper_type, **model_mapper_kwargs)
    
    logger.info(f"Mapping models from {input_dir} to API schema and saving to {output_dir}")
    
    # Run model mapping
    result = model_mapper.map_directory(input_dir, output_dir)
    
    # Check result
    if result["success"]:
        logger.info(f"Model mapping completed successfully")
        if "mapped_models" in result:
            logger.info(f"Mapped {len(result['mapped_models'])} models to API schema")
            for model_path in result.get("mapped_models", []):
                logger.info(f"  - {model_path}")
        exit_code = 0
    else:
        error = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"Model mapping failed: {error}")
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
