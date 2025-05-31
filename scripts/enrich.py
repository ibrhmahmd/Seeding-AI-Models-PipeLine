#!/usr/bin/env python
"""
CLI script for enriching model data with additional metadata.

This script provides a command-line interface for enriching model data
extracted from various sources with additional metadata.
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
        description="Enrich model data with additional metadata",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Input/Output directories
    parser.add_argument(
        "--input-dir", 
        type=str,
        help="Directory containing raw model data files"
    )
    parser.add_argument(
        "--output-dir", 
        type=str,
        help="Directory to save enriched model data"
    )
    
    # Enricher options
    parser.add_argument(
        "--enricher-type",
        choices=["metadata", "huggingface"],
        default="metadata",
        help="Type of enricher to use"
    )
    
    # HuggingFace options
    parser.add_argument(
        "--hf-api-key",
        type=str,
        help="HuggingFace API key (for HuggingFace enricher)"
    )
    
    # General options
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the enrichment script."""
    args = parse_args()
    
    # Configure logging
    # Note: The PipelineLogger doesn't take a level parameter in get_logger
    # We'll use the default log level from config
    logger = get_logger("EnricherCLI")
    logger.info("Starting model enrichment")
    
    # Get configuration
    config = get_config()
    
    # Determine input/output directories
    input_dir = args.input_dir or str(config.raw_data_dir)
    output_dir = args.output_dir or str(config.enriched_data_dir)
    
    # Create enricher with additional options
    factory = PipelineFactory(logger=logger)
    enricher_kwargs = {"logger": logger}
    
    # Add HuggingFace API key if specified
    if args.enricher_type == "huggingface" and args.hf_api_key:
        enricher_kwargs["api_key"] = args.hf_api_key
    
    enricher = factory.create_enricher(args.enricher_type, **enricher_kwargs)
    
    logger.info(f"Enriching models from {input_dir} and saving to {output_dir}")
    
    # Run enrichment
    result = enricher.enrich_directory(input_dir, output_dir)
    
    # Check result
    if result["success"]:
        logger.info(f"Enrichment completed successfully")
        if "enriched_models" in result:
            logger.info(f"Enriched {len(result['enriched_models'])} models")
            for model_path in result.get("enriched_models", []):
                logger.info(f"  - {model_path}")
        exit_code = 0
    else:
        error = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"Enrichment failed: {error}")
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
