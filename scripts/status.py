#!/usr/bin/env python
"""
Utility script for checking pipeline status.

This script provides a command-line utility for checking the status of the
pipeline, including file counts, directory sizes, and last processed models.
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add the parent directory to the path so we can import pipeline modules
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from pipeline.config import get_config
from pipeline.logger import get_logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Check pipeline status",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Status options
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed status information"
    )
    parser.add_argument(
        "--show-latest",
        type=int,
        default=3,
        help="Number of latest models to show for each stage"
    )
    
    # Output options
    parser.add_argument(
        "--output-file",
        type=str,
        help="File to write status to (JSON format)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    
    # General options
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def get_directory_stats(directory: Path) -> Dict[str, Any]:
    """
    Get statistics for a directory.
    
    Args:
        directory: Path to the directory.
        
    Returns:
        Dictionary containing directory statistics.
    """
    if not directory.exists():
        return {
            "exists": False,
            "file_count": 0,
            "size_bytes": 0,
            "latest_files": []
        }
    
    # Get all JSON files
    json_files = list(directory.glob("**/*.json"))
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in json_files if f.is_file())
    
    # Get latest files
    latest_files = []
    for file_path in json_files:
        if file_path.is_file():
            latest_files.append((
                file_path,
                file_path.stat().st_mtime
            ))
    
    # Sort by modification time (newest first)
    latest_files.sort(key=lambda x: x[1], reverse=True)
    
    return {
        "exists": True,
        "file_count": len(json_files),
        "size_bytes": total_size,
        "latest_files": [
            {
                "path": str(f[0]),
                "modified_at": datetime.datetime.fromtimestamp(f[1]).isoformat(),
                "size_bytes": f[0].stat().st_size
            }
            for f in latest_files
        ]
    }


def format_size(size_bytes: int) -> str:
    """
    Format a size in bytes to a human-readable string.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Human-readable size string.
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def main():
    """Main entry point for the status script."""
    args = parse_args()
    
    # Configure logging
    # Note: The PipelineLogger doesn't take a level parameter in get_logger
    # We'll use the default log level from config
    logger = get_logger("StatusUtility")
    logger.info("Checking pipeline status")
    
    # Get configuration
    config = get_config()
    
    # Get directory stats
    raw_stats = get_directory_stats(Path(config.raw_data_dir))
    enriched_stats = get_directory_stats(Path(config.enriched_data_dir))
    processed_stats = get_directory_stats(Path(config.processed_data_dir))
    mapped_stats = get_directory_stats(Path(config.mapped_data_dir))
    archive_stats = get_directory_stats(Path(config.archive_dir))
    
    # Build status object
    status = {
        "timestamp": datetime.datetime.now().isoformat(),
        "directories": {
            "raw": {
                "path": str(config.raw_data_dir),
                "file_count": raw_stats["file_count"],
                "size_bytes": raw_stats["size_bytes"],
                "size_formatted": format_size(raw_stats["size_bytes"]),
                "exists": raw_stats["exists"]
            },
            "enriched": {
                "path": str(config.enriched_data_dir),
                "file_count": enriched_stats["file_count"],
                "size_bytes": enriched_stats["size_bytes"],
                "size_formatted": format_size(enriched_stats["size_bytes"]),
                "exists": enriched_stats["exists"]
            },
            "processed": {
                "path": str(config.processed_data_dir),
                "file_count": processed_stats["file_count"],
                "size_bytes": processed_stats["size_bytes"],
                "size_formatted": format_size(processed_stats["size_bytes"]),
                "exists": processed_stats["exists"]
            },
            "mapped": {
                "path": str(config.mapped_data_dir),
                "file_count": mapped_stats["file_count"],
                "size_bytes": mapped_stats["size_bytes"],
                "size_formatted": format_size(mapped_stats["size_bytes"]),
                "exists": mapped_stats["exists"]
            },
            "archive": {
                "path": str(config.archive_dir),
                "file_count": archive_stats["file_count"],
                "size_bytes": archive_stats["size_bytes"],
                "size_formatted": format_size(archive_stats["size_bytes"]),
                "exists": archive_stats["exists"]
            }
        }
    }
    
    # Add latest files if detailed
    if args.detailed:
        show_latest = max(0, args.show_latest)
        for stage, stats in [
            ("raw", raw_stats),
            ("enriched", enriched_stats),
            ("processed", processed_stats),
            ("mapped", mapped_stats),
            ("archive", archive_stats)
        ]:
            if stats["exists"] and stats["file_count"] > 0:
                status["directories"][stage]["latest_files"] = stats["latest_files"][:show_latest]
    
    # Output in JSON format if requested
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        # Print formatted status
        print("\nPipeline Status")
        print("==============")
        print(f"Timestamp: {status['timestamp']}")
        
        print("\nDirectory Status:")
        for stage, stage_status in status["directories"].items():
            exists_str = "Exists" if stage_status["exists"] else "Missing"
            print(f"  {stage.capitalize()} ({exists_str}):")
            print(f"    Path: {stage_status['path']}")
            print(f"    Files: {stage_status['file_count']}")
            print(f"    Size: {stage_status['size_formatted']}")
            
            # Print latest files if detailed
            if args.detailed and stage_status["exists"] and "latest_files" in stage_status:
                if stage_status["latest_files"]:
                    print("\n    Latest Files:")
                    for file_info in stage_status["latest_files"]:
                        file_path = Path(file_info["path"]).name
                        modified = file_info["modified_at"]
                        size = format_size(file_info["size_bytes"])
                        print(f"      - {file_path} ({size}, {modified})")
                    print()
    
    # Write to file if requested
    if args.output_file:
        output_path = Path(args.output_file)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2)
            
            logger.info(f"Status written to {output_path}")
            if not args.json:
                print(f"\nStatus written to {output_path}")
        except Exception as e:
            logger.error(f"Error writing status: {e}")
            print(f"Error writing status: {e}")


if __name__ == "__main__":
    main()
