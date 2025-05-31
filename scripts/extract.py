#!/usr/bin/env python
"""
CLI script for extracting model data from sources.

This script provides a command-line interface for extracting model data from 
various sources and saving it to the raw data directory.
"""

import argparse
import json
import os
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
        description="Extract model data from sources",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Source configuration
    parser.add_argument(
        "--source-config", 
        type=str,
        help="Path to a JSON file with source configuration"
    )
    
    parser.add_argument(
        "--source-type",
        choices=["ollama", "json"],
        default="ollama",
        help="Type of source to extract from"
    )
    
    # Output directory
    parser.add_argument(
        "--output-dir", 
        type=str,
        help="Directory to save extracted model data"
    )
    
    # Options for Ollama extraction
    parser.add_argument(
        "--ollama-url",
        type=str,
        help="URL for Ollama API (for Ollama extraction)"
    )
    
    # Options for JSON file extraction
    parser.add_argument(
        "--input-dir",
        type=str,
        help="Input directory containing JSON files (for JSON extraction)"
    )
    
    # General options
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the extraction script."""
    args = parse_args()
    
    # Configure logging
    # Note: The PipelineLogger doesn't take a level parameter in get_logger
    # We'll use the default log level from config
    logger = get_logger("ExtractorCLI")
    logger.info("Starting model extraction")
    
    # Get configuration
    config = get_config()
    
    # Build source configuration
    source_config = {}
    
    if args.source_config:
        try:
            with open(args.source_config, 'r') as f:
                source_config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading source config file: {e}")
            sys.exit(1)
    else:
        # Build source configuration based on source type
        if args.source_type == "ollama":
            source_config["type"] = "ollama"
            source_config["url"] = args.ollama_url or os.getenv("OLLAMA_API_URL", "http://localhost:11434/api")
        elif args.source_type == "json":
            source_config["type"] = "json"
            source_config["input_dir"] = args.input_dir or str(config.data_dir / "input")
    
    # Determine output directory
    output_dir = Path(args.output_dir or str(config.raw_data_dir))
    
    # Create output directory if it doesn't exist
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")
    except Exception as e:
        logger.error(f"Failed to create output directory {output_dir}: {str(e)}")
        raise

    # Create and run extractor
    factory = PipelineFactory(logger=logger)
    extractor = factory.create_extractor(args.source_type, logger=logger)
    source_config = {}
    if args.source_type == "ollama":
        source_config["use_cli"] = False  # Force API usage if CLI is not available
        source_config["api_url"] = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        logger.info("Using Ollama API directly (CLI disabled)")
    if args.input_dir and "input_dir" in source_config:
        source_config["input_dir"] = args.input_dir or str(config.data_dir / "input")

    # Determine output directory
    output_dir = Path(args.output_dir or str(config.raw_data_dir))
    
    logger.info(f"Extracting from {args.source_type} source to {output_dir}")
    
    # Run extraction
    try:
        result = extractor.extract_from_source(source_config, output_dir)
        logger.info(f"Extraction result: {result}")
        if result.get('success', False):
            models = result.get('models', [])
            logger.info(f"Retrieved {len(models)} models from Ollama API")
            for model in models:
                model_name = model.get('name', 'Unknown')
                logger.info(f"Model: {model_name}")
                # Sanitize model name for file writing
                safe_model_name = model_name.replace(':', '_').replace('.', '_').replace('-', '_')
                logger.info(f"Sanitized model name for file: {safe_model_name}")
            raw_response = result.get('raw_response', {})
            logger.info(f"Raw Ollama API response: {raw_response}")
            if len(models) == 0:
                logger.warning("No models data retrieved to write to files")
            else:
                logger.info("Data retrieved, should be written to files")
            extracted_models = result.get('extracted_models', [])
            logger.info(f"Attempted to write {len(extracted_models)} model files")
            for path in extracted_models:
                logger.info(f"Wrote model data to: {path}")
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        logger.exception("Detailed exception information:")
        raise
    
    # Check result
    if result["success"]:
        logger.info(f"Extraction completed successfully")
        if "extracted_models" in result:
            logger.info(f"Extracted {len(result['extracted_models'])} models")
            for model_path in result.get("extracted_models", []):
                logger.info(f"  - {model_path}")
        exit_code = 0
    else:
        error = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"Extraction failed: {error}")
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
