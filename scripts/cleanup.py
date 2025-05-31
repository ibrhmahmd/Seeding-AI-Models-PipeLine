#!/usr/bin/env python
"""
Utility script for cleaning up temporary and processed files.

This script provides a command-line utility for cleaning up temporary files,
clearing output directories, and managing the pipeline's working directories.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

# Add the parent directory to the path so we can import pipeline modules
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from pipeline.config import get_config
from pipeline.logger import get_logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Clean up temporary and processed files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Cleanup options
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean all pipeline directories"
    )
    
    # Specific directories
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Clean raw data directory"
    )
    parser.add_argument(
        "--enriched",
        action="store_true",
        help="Clean enriched data directory"
    )
    parser.add_argument(
        "--processed",
        action="store_true",
        help="Clean processed data directory"
    )
    parser.add_argument(
        "--mapped",
        action="store_true",
        help="Clean API-mapped data directory"
    )
    
    # Other options
    parser.add_argument(
        "--logs",
        action="store_true",
        help="Clean log files"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force cleanup without confirmation"
    )
    
    # General options
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def clean_directory(directory: Path, force: bool = False, verbose: bool = False, logger=None):
    """
    Clean a directory by removing all files and subdirectories.
    
    Args:
        directory: Path to the directory to clean.
        force: If True, clean without confirmation.
        verbose: If True, print verbose output.
        logger: Logger for logging events.
        
    Returns:
        True if cleaning was successful, False otherwise.
    """
    if not directory.exists():
        if logger:
            logger.info(f"Directory does not exist: {directory}")
        return True
    
    if not directory.is_dir():
        if logger:
            logger.error(f"Not a directory: {directory}")
        return False
    
    # Get list of items to delete
    items = list(directory.glob("*"))
    
    if not items:
        if logger:
            logger.info(f"Directory already empty: {directory}")
        return True
    
    # Ask for confirmation if not forced
    if not force:
        print(f"\nAbout to delete {len(items)} items from {directory}")
        confirmation = input("Are you sure you want to proceed? (y/N) ").lower()
        if confirmation not in ["y", "yes"]:
            if logger:
                logger.info("Cleanup cancelled by user")
            print("Cleanup cancelled.")
            return False
    
    # Delete all items
    for item in items:
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    
    if logger:
        logger.info(f"Cleaned directory: {directory}")
    
    return True


def main():
    """Main entry point for the cleanup script."""
    args = parse_args()
    
    # Configure logging
    # Note: The PipelineLogger doesn't take a level parameter in get_logger
    # We'll use the default log level from config
    logger = get_logger("CleanupUtility")
    logger.info("Starting cleanup utility")
    
    # Get configuration
    config = get_config()
    
    # Determine which directories to clean
    directories_to_clean = []
    
    if args.all:
        directories_to_clean.extend([
            (config.raw_data_dir, "raw data"),
            (config.enriched_data_dir, "enriched data"),
            (config.processed_data_dir, "processed data"),
            (config.mapped_data_dir, "mapped data")
        ])
    else:
        if args.raw:
            directories_to_clean.append((config.raw_data_dir, "raw data"))
        if args.enriched:
            directories_to_clean.append((config.enriched_data_dir, "enriched data"))
        if args.processed:
            directories_to_clean.append((config.processed_data_dir, "processed data"))
        if args.mapped:
            directories_to_clean.append((config.mapped_data_dir, "mapped data"))
    
    # Add log directory if requested
    if args.logs:
        log_dir = Path(config.log_file).parent
        directories_to_clean.append((log_dir, "logs"))
    
    # Check if any directories were selected
    if not directories_to_clean:
        logger.warning("No directories selected for cleanup")
        print("No directories selected for cleanup. Use --help for options.")
        return
    
    # Clean each directory
    success = True
    
    for directory, name in directories_to_clean:
        print(f"Cleaning {name} directory: {directory}")
        result = clean_directory(directory, args.force, args.verbose, logger)
        if not result:
            success = False
    
    if success:
        logger.info("Cleanup completed successfully")
        print("\nCleanup completed successfully.")
    else:
        logger.warning("Cleanup completed with some errors")
        print("\nCleanup completed with some errors.")


if __name__ == "__main__":
    main()
