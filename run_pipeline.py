#!/usr/bin/env python
"""
Main runner script for the AI Model Seeding Pipeline.

This script provides the command-line interface for running
the AI Model Seeding Pipeline.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from pipeline.config import get_config
from pipeline.factory import PipelineFactory
from pipeline.logger import get_logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Model Seeding Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Basic configuration
    parser.add_argument(
        "--config", 
        type=str,
        help="Path to a JSON configuration file"
    )
    
    # Pipeline component selection
    parser.add_argument(
        "--extractor", 
        choices=["ollama", "json"], 
        help="Type of extractor to use"
    )
    parser.add_argument(
        "--enricher", 
        choices=["metadata", "huggingface"], 
        help="Type of enricher to use"
    )
    parser.add_argument(
        "--tag-mapper", 
        choices=["simple", "fallback"], 
        help="Type of tag mapper to use"
    )
    parser.add_argument(
        "--model-mapper", 
        choices=["standard"], 
        help="Type of model mapper to use"
    )
    parser.add_argument(
        "--seeder", 
        choices=["api", "mock"], 
        help="Type of seeder to use"
    )
    parser.add_argument(
        "--archiver", 
        choices=["simple", "organized", "metadata"], 
        help="Type of archiver to use"
    )
    
    # Source configuration
    parser.add_argument(
        "--source-config", 
        type=str,
        help="Path to a JSON file with source configuration"
    )
    
    # Directory configuration
    parser.add_argument(
        "--raw-dir", 
        type=str,
        help="Directory for raw data files"
    )
    parser.add_argument(
        "--enriched-dir", 
        type=str,
        help="Directory for enriched data files"
    )
    parser.add_argument(
        "--processed-dir", 
        type=str,
        help="Directory for processed data files"
    )
    parser.add_argument(
        "--mapped-dir", 
        type=str,
        help="Directory for API-mapped data files"
    )
    parser.add_argument(
        "--archive-dir", 
        type=str,
        help="Directory for archived files"
    )
    
    # API configuration
    parser.add_argument(
        "--api-url", 
        type=str,
        help="API endpoint URL"
    )
    parser.add_argument(
        "--api-key", 
        type=str,
        help="API authentication key"
    )
    
    # Tag mapping configuration
    parser.add_argument(
        "--tag-map-file", 
        type=str,
        help="Path to the tag mapping file"
    )
    
    # Execution options
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Validate the pipeline but don't execute it"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--phase", 
        choices=[
            "extract", 
            "enrich", 
            "map_tags", 
            "map_models", 
            "seed", 
            "archive",
            "all"
        ],
        default="all",
        help="Run only the specified phase(s)"
    )
    
    return parser.parse_args()


def build_pipeline_config(args) -> Dict[str, Any]:
    """
    Build the pipeline configuration from command line arguments.
    
    Args:
        args: Command line arguments.
        
    Returns:
        Pipeline configuration dictionary.
    """
    config = get_config()
    pipeline_config = {}
    
    # Load from config file if specified
    if args.config:
        try:
            with open(args.config, 'r') as f:
                file_config = json.load(f)
                pipeline_config.update(file_config)
        except Exception as e:
            print(f"Error loading config file: {e}")
            sys.exit(1)
    
    # Pipeline component selection
    if args.extractor:
        pipeline_config["extractor_type"] = args.extractor
    if args.enricher:
        pipeline_config["enricher_type"] = args.enricher
    if args.tag_mapper:
        pipeline_config["tag_mapper_type"] = args.tag_mapper
    if args.model_mapper:
        pipeline_config["model_mapper_type"] = args.model_mapper
    if args.seeder:
        pipeline_config["seeder_type"] = args.seeder
    if args.archiver:
        pipeline_config["archiver_type"] = args.archiver
    
    # Source configuration
    if args.source_config:
        try:
            with open(args.source_config, 'r') as f:
                source_config = json.load(f)
                pipeline_config["source_config"] = source_config
        except Exception as e:
            print(f"Error loading source config file: {e}")
            sys.exit(1)
    
    # Directory configuration
    if args.raw_dir:
        pipeline_config["raw_data_dir"] = args.raw_dir
    if args.enriched_dir:
        pipeline_config["enriched_data_dir"] = args.enriched_dir
    if args.processed_dir:
        pipeline_config["processed_data_dir"] = args.processed_dir
    if args.mapped_dir:
        pipeline_config["mapped_data_dir"] = args.mapped_dir
    if args.archive_dir:
        pipeline_config["archive_dir"] = args.archive_dir
    
    # API configuration
    if args.api_url:
        pipeline_config["api_url"] = args.api_url
    if args.api_key:
        pipeline_config["api_key"] = args.api_key
    
    # Tag mapping configuration
    if args.tag_map_file:
        pipeline_config["tag_map_file"] = args.tag_map_file
    
    return pipeline_config


def main():
    """Main entry point for the pipeline."""
    args = parse_args()
    
    # Configure logging
    log_level = "DEBUG" if args.verbose else None
    logger = get_logger("MainPipeline", level=log_level)
    logger.info("Starting AI Model Seeding Pipeline")
    
    # Build the pipeline configuration
    pipeline_config = build_pipeline_config(args)
    
    # Create the pipeline
    factory = PipelineFactory(logger=logger)
    pipeline = factory.create_pipeline(pipeline_config)
    
    if args.dry_run:
        logger.info("Dry run complete, pipeline assembled but not executed")
        sys.exit(0)
    
    # Run the pipeline
    if args.phase == "all":
        logger.info("Running complete pipeline")
        result = pipeline.run(pipeline_config)
    else:
        logger.info(f"Running pipeline phase: {args.phase}")
        input_data = {
            "source_config": pipeline_config.get("source_config", {}),
            "input_dir": pipeline_config.get(f"{args.phase}_dir"),
            "output_dir": pipeline_config.get(f"{args.phase}_dir")
        }
        
        if args.phase == "seed":
            input_data["api_url"] = pipeline_config.get("api_url")
            input_data["api_key"] = pipeline_config.get("api_key")
        elif args.phase == "map_tags":
            input_data["tag_map_file"] = pipeline_config.get("tag_map_file")
            
        result = pipeline.run_phase(args.phase, input_data)
    
    # Print results
    if result["success"]:
        logger.info("Pipeline execution completed successfully")
        exit_code = 0
    else:
        error = result.get("error", {}).get("message", "Unknown error")
        logger.error(f"Pipeline execution failed: {error}")
        exit_code = 1
    
    # Print summary
    print("\nPipeline execution summary:")
    print(f"Status: {'Success' if result['success'] else 'Failed'}")
    if "results" in result:
        for phase, phase_result in result["results"].items():
            success = phase_result.get("success", False)
            status = "Success" if success else "Failed"
            print(f"  {phase}: {status}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
