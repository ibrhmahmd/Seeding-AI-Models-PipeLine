#!/usr/bin/env python
"""
Main runner script for the AI Model Seeding Pipeline.

This script provides the command-line interface for running
the AI Model Seeding Pipeline.
"""

import argparse
import json
import os
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
    parser.add_argument(
        "--skip-extract", 
        action="store_true",
        help="Skip the data extraction stage"
    )
    parser.add_argument(
        "--skip-enrich", 
        action="store_true",
        help="Skip the data enrichment stage"
    )
    parser.add_argument(
        "--skip-tag-map", 
        action="store_true",
        help="Skip the tag mapping stage"
    )
    parser.add_argument(
        "--skip-model-map", 
        action="store_true",
        help="Skip the model mapping stage"
    )
    parser.add_argument(
        "--skip-seed", 
        action="store_true",
        help="Skip the data seeding stage"
    )
    parser.add_argument(
        "--skip-archive", 
        action="store_true",
        help="Skip the data archiving stage"
    )
    parser.add_argument(
        "--continue-on-error", 
        action="store_true",
        help="Continue pipeline execution even if a stage fails"
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


def run_component(component, method, stage_name, logger):
    try:
        result = method(component)
        logger.info(f"{stage_name.capitalize()} stage completed successfully")
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"{stage_name.capitalize()} stage failed: {e}")
        return {"success": False, "error": {"message": str(e)}}


def main():
    """Main entry point for the pipeline."""
    args = parse_args()
    
    # Configure logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = get_logger("MainPipeline")
    logger.info(f"Starting AI model seeding pipeline (log level: {log_level})")
    
    # Build the pipeline configuration
    pipeline_config = build_pipeline_config(args)
    
    # Create the pipeline
    factory = PipelineFactory(logger=logger)
    pipeline = factory.create_pipeline(pipeline_config)
    
    summary = {}
    
    # Stage 1: Data Extraction
    if not args.skip_extract:
        logger.info("Running data extraction stage...")
        extractor_type = os.environ.get("DEFAULT_EXTRACTOR_TYPE", "ollama")
        extractor = factory.create_extractor(extractor_type, logger=logger)
        source_config = {}
        if extractor_type == "ollama":
            source_config["use_cli"] = False
            source_config["api_url"] = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
            logger.info("Using Ollama API directly (CLI disabled)")
        raw_data_dir = Path(os.environ.get("RAW_DATA_DIR", "./data/raw"))
        result = run_component(
            component=extractor,
            method=lambda c: c.extract_from_source(source_config, raw_data_dir),
            stage_name="extract",
            logger=logger
        )
        if not result["success"]:
            summary["extract"] = "Failed"
            summary["overall"] = "Failed"
            logger.error(f"Extraction stage failed: {result.get('error', 'Unknown error')}")
            if not args.continue_on_error:
                sys.exit(1)
        else:
            summary["extract"] = "Success"
            logger.info("Data extraction completed successfully")

    # Stage 2: Data Enrichment
    if not args.skip_enrich and summary.get("extract", "Failed") == "Success":
        logger.info("Running data enrichment stage...")
        enricher_type = os.environ.get("DEFAULT_ENRICHER_TYPE", "default")
        enricher = factory.create_enricher(enricher_type, logger=logger)
        raw_data_dir = Path(os.environ.get("RAW_DATA_DIR", "./data/raw"))
        enriched_data_dir = Path(os.environ.get("ENRICHED_DATA_DIR", "./data/enriched"))
        result = run_component(
            component=enricher,
            method=lambda c: c.enrich_data(raw_data_dir, enriched_data_dir),
            stage_name="enrich",
            logger=logger
        )
        if not result["success"]:
            summary["enrich"] = "Failed"
            summary["overall"] = "Failed"
            logger.error(f"Enrichment stage failed: {result.get('error', 'Unknown error')}")
            if not args.continue_on_error:
                sys.exit(1)
        else:
            summary["enrich"] = "Success"
            logger.info("Data enrichment completed successfully")

    # Stage 3: Tag Mapping
    if not args.skip_tag_map and summary.get("enrich", "Failed") == "Success":
        logger.info("Running tag mapping stage...")
        tag_mapper_type = os.environ.get("DEFAULT_TAG_MAPPER_TYPE", "simple")
        tag_mapper = factory.create_tag_mapper(tag_mapper_type, logger=logger)
        enriched_data_dir = Path(os.environ.get("ENRICHED_DATA_DIR", "./data/enriched"))
        processed_data_dir = Path(os.environ.get("PROCESSED_DATA_DIR", "./data/processed"))
        result = run_component(
            component=tag_mapper,
            method=lambda c: c.map_tags(enriched_data_dir, processed_data_dir),
            stage_name="tag_map",
            logger=logger
        )
        if not result["success"]:
            summary["tag_map"] = "Failed"
            summary["overall"] = "Failed"
            logger.error(f"Tag mapping stage failed: {result.get('error', 'Unknown error')}")
            if not args.continue_on_error:
                sys.exit(1)
        else:
            summary["tag_map"] = "Success"
            logger.info("Tag mapping completed successfully")

    # Stage 4: Model Mapping
    if not args.skip_model_map and summary.get("tag_map", "Failed") == "Success":
        logger.info("Running model mapping stage...")
        model_mapper_type = os.environ.get("DEFAULT_MODEL_MAPPER_TYPE", "api")
        model_mapper = factory.create_model_mapper(model_mapper_type, logger=logger)
        processed_data_dir = Path(os.environ.get("PROCESSED_DATA_DIR", "./data/processed"))
        mapped_data_dir = Path(os.environ.get("MAPPED_DATA_DIR", "./data/mapped"))
        result = run_component(
            component=model_mapper,
            method=lambda c: c.map_models(processed_data_dir, mapped_data_dir),
            stage_name="model_map",
            logger=logger
        )
        if not result["success"]:
            summary["model_map"] = "Failed"
            summary["overall"] = "Failed"
            logger.error(f"Model mapping stage failed: {result.get('error', 'Unknown error')}")
            if not args.continue_on_error:
                sys.exit(1)
        else:
            summary["model_map"] = "Success"
            logger.info("Model mapping completed successfully")

    # Stage 5: Data Seeding
    if not args.skip_seed and summary.get("model_map", "Failed") == "Success":
        logger.info("Running data seeding stage...")
        seeder_type = os.environ.get("DEFAULT_SEEDER_TYPE", "mock")
        seeder = factory.create_seeder(seeder_type, logger=logger)
        mapped_data_dir = Path(os.environ.get("MAPPED_DATA_DIR", "./data/mapped"))
        result = run_component(
            component=seeder,
            method=lambda c: c.seed_data(mapped_data_dir, dry_run=args.dry_run),
            stage_name="seed",
            logger=logger
        )
        if not result["success"]:
            summary["seed"] = "Failed"
            summary["overall"] = "Failed"
            logger.error(f"Seeding stage failed: {result.get('error', 'Unknown error')}")
            if not args.continue_on_error:
                sys.exit(1)
        else:
            summary["seed"] = "Success"
            logger.info("Data seeding completed successfully")

    # Stage 6: Data Archiving
    if not args.skip_archive and summary.get("seed", "Failed") == "Success":
        logger.info("Running data archiving stage...")
        archiver_type = os.environ.get("DEFAULT_ARCHIVER_TYPE", "file")
        archiver = factory.create_archiver(archiver_type, logger=logger)
        mapped_data_dir = Path(os.environ.get("MAPPED_DATA_DIR", "./data/mapped"))
        archive_dir = Path(os.environ.get("ARCHIVE_DIR", "./archive"))
        result = run_component(
            component=archiver,
            method=lambda c: c.archive_data(mapped_data_dir, archive_dir),
            stage_name="archive",
            logger=logger
        )
        if not result["success"]:
            summary["archive"] = "Failed"
            summary["overall"] = "Failed"
            logger.error(f"Archiving stage failed: {result.get('error', 'Unknown error')}")
        else:
            summary["archive"] = "Success"
            logger.info("Data archiving completed successfully")
    
    # Print summary
    print("\nPipeline execution summary:")
    print(f"Status: {'Success' if summary.get('overall', 'Failed') == 'Success' else 'Failed'}")
    for stage, status in summary.items():
        if stage != "overall":
            print(f"  {stage}: {status}")
    
    if summary.get("overall", "Failed") == "Failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
