#!/usr/bin/env python
"""
CLI script for archiving processed model data files.

This script provides a command-line interface for archiving processed model data files
to prevent reprocessing and maintain a clean workspace.
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
        description="Archive processed model data files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Input/Output directories
    parser.add_argument(
        "--input-dir", 
        type=str,
        help="Directory containing files to archive"
    )
    parser.add_argument(
        "--archive-dir", 
        type=str,
        help="Directory to move archived files to"
    )
    
    # Archiver options
    parser.add_argument(
        "--archiver-type",
        choices=["simple", "organized", "metadata"],
        default="metadata",
        help="Type of archiver to use"
    )
    parser.add_argument(
        "--organize-by-date",
        action="store_true",
        help="Organize archived files by date (for organized archiver)"
    )
    parser.add_argument(
        "--include-timestamp",
        action="store_true",
        help="Include timestamp in archived file names"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Glob pattern to filter files for archiving"
    )
    
    # General options
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the archiving script."""
    args = parse_args()
    
    # Configure logging
    # Note: The PipelineLogger doesn't take a level parameter in get_logger
    # We'll use the default log level from config
    logger = get_logger("ArchiverCLI")
    logger.info("Starting file archiving")
    
    # Get configuration
    config = get_config()
    
    # Determine input/archive directories
    input_dir = args.input_dir or str(config.mapped_data_dir)
    archive_dir = args.archive_dir or str(config.archive_dir)
    
    # Create archiver with additional options
    factory = PipelineFactory(logger=logger)
    archiver_kwargs = {
        "logger": logger,
    }
    
    if args.archiver_type == "organized":
        archiver_kwargs["organize_by_date"] = args.organize_by_date
        archiver_kwargs["include_timestamp"] = args.include_timestamp
    
    archiver = factory.create_archiver(args.archiver_type, **archiver_kwargs)
    
    logger.info(f"Archiving files from {input_dir} to {archive_dir}")
    
    # Run archiving
    result = archiver.archive_directory(input_dir, archive_dir, pattern=args.pattern)
    
    # Check result
    if result["success"]:
        logger.info(f"Archiving completed successfully")
        if "archived_files" in result:
            logger.info(f"Archived {len(result['archived_files'])} files")
            for file_path in result.get("archived_files", []):
                logger.info(f"  - {file_path}")
        exit_code = 0
    else:
        error = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"Archiving failed: {error}")
        
        if "failed_files" in result:
            logger.error(f"Failed to archive {len(result['failed_files'])} files:")
            for failed in result.get("failed_files", []):
                file_path = failed.get("file", "unknown")
                error_msg = failed.get("error", "Unknown error")
                logger.error(f"  - {file_path}: {error_msg}")
        
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
