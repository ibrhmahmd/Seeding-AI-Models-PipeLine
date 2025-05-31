#!/usr/bin/env python
"""
CLI script for seeding models to the API.

This script provides a command-line interface for seeding API-ready model data
to the target API endpoint.
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
        description="Seed models to the API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Input directory
    parser.add_argument(
        "--input-dir", 
        type=str,
        help="Directory containing API-ready model data files"
    )
    
    # API options
    parser.add_argument(
        "--api-url",
        type=str,
        help="URL for the API endpoint"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="API key for authentication"
    )
    
    # Seeder options
    parser.add_argument(
        "--seeder-type",
        choices=["api", "mock"],
        default="api",
        help="Type of seeder to use"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Number of models to seed in each batch"
    )
    parser.add_argument(
        "--delay",
        type=float,
        help="Delay between API calls in seconds"
    )
    parser.add_argument(
        "--retry-attempts",
        type=int,
        help="Number of retry attempts for failed API calls"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Timeout for API calls in seconds"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate but don't actually send to API"
    )
    
    # General options
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the seeding script."""
    args = parse_args()
    
    # Configure logging
    # Note: The PipelineLogger doesn't take a level parameter in get_logger
    # We'll use the default log level from config
    logger = get_logger("SeederCLI")
    logger.info("Starting model seeding to API")
    
    # Get configuration
    config = get_config()
    
    # Determine input directory and API settings
    input_dir = args.input_dir or str(config.mapped_data_dir)
    api_url = args.api_url or config.api_url
    api_key = args.api_key or config.api_key
    
    # Create seeder with additional options
    factory = PipelineFactory(logger=logger)
    seeder_kwargs = {
        "logger": logger,
    }
    
    if args.batch_size:
        seeder_kwargs["batch_size"] = args.batch_size
    if args.delay:
        seeder_kwargs["delay"] = args.delay
    if args.retry_attempts:
        seeder_kwargs["retry_attempts"] = args.retry_attempts
    if args.timeout:
        seeder_kwargs["timeout"] = args.timeout
    
    # Use mock seeder if in dry-run mode
    seeder_type = "mock" if args.dry_run else args.seeder_type
    seeder = factory.create_seeder(seeder_type, **seeder_kwargs)
    
    if args.dry_run:
        logger.info("DRY RUN MODE - Models will not be sent to API")
    
    logger.info(f"Seeding models from {input_dir} to API at {api_url}")
    
    # Run seeding
    result = seeder.seed_directory(input_dir, api_url, api_key)
    
    # Check result
    if result["success"]:
        logger.info(f"Seeding completed successfully")
        if "seeded_models" in result:
            logger.info(f"Seeded {len(result['seeded_models'])} models to API")
            for model_info in result.get("seeded_models", []):
                model_id = model_info.get("modelId", "unknown")
                response = model_info.get("response", {})
                status = response.get("status", "unknown")
                logger.info(f"  - {model_id}: {status}")
        exit_code = 0
    else:
        error = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"Seeding failed: {error}")
        
        if "failed_models" in result:
            logger.error(f"Failed to seed {len(result['failed_models'])} models:")
            for failed in result.get("failed_models", []):
                model_id = failed.get("modelId", "unknown")
                error_msg = failed.get("error", {}).get("message", "Unknown error")
                logger.error(f"  - {model_id}: {error_msg}")
        
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
