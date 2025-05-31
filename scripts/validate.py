#!/usr/bin/env python
"""
Utility script for validating model data files.

This script provides a command-line utility for validating model data files
against their expected schemas at each stage of the pipeline.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Add the parent directory to the path so we can import pipeline modules
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from pipeline.config import get_config
from pipeline.logger import get_logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate model data files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Input directory
    parser.add_argument(
        "input_path",
        type=str,
        help="Directory or file to validate"
    )
    
    # Validation type
    parser.add_argument(
        "--stage",
        choices=["raw", "enriched", "tagged", "api", "auto"],
        default="auto",
        help="Pipeline stage to validate against"
    )
    
    # Output options
    parser.add_argument(
        "--output-file",
        type=str,
        help="File to write validation results to (JSON format)"
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only output a summary of validation results"
    )
    
    # General options
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def validate_raw_model(model_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a raw model data file.
    
    Args:
        model_data: The model data to validate.
        
    Returns:
        Dictionary containing validation results.
    """
    errors = []
    warnings = []
    
    # Check required fields
    if "name" not in model_data:
        errors.append("Missing required field: name")
    elif not isinstance(model_data["name"], str):
        errors.append("Field 'name' must be a string")
    
    if "modelId" not in model_data:
        warnings.append("Missing recommended field: modelId")
    
    # Check for description
    if "description" not in model_data:
        warnings.append("Missing recommended field: description")
    elif not isinstance(model_data["description"], str):
        warnings.append("Field 'description' should be a string")
    
    # Check tags if present
    if "tags" in model_data:
        if not isinstance(model_data["tags"], list):
            errors.append("Field 'tags' must be an array")
        else:
            for i, tag in enumerate(model_data["tags"]):
                if not isinstance(tag, str):
                    errors.append(f"Tag at index {i} must be a string")
    
    # Check parameters if present
    if "parameters" in model_data and not isinstance(model_data["parameters"], dict):
        errors.append("Field 'parameters' must be an object")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stage": "raw"
    }


def validate_enriched_model(model_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate an enriched model data file.
    
    Args:
        model_data: The model data to validate.
        
    Returns:
        Dictionary containing validation results.
    """
    # First validate as a raw model
    result = validate_raw_model(model_data)
    errors = result["errors"].copy()
    warnings = result["warnings"].copy()
    
    # Check enrichment fields
    if "metadata" not in model_data:
        warnings.append("Missing enrichment field: metadata")
    elif not isinstance(model_data["metadata"], dict):
        errors.append("Field 'metadata' must be an object")
    
    # Check for created/updated timestamps
    if "createdAt" not in model_data:
        warnings.append("Missing recommended field: createdAt")
    
    if "updatedAt" not in model_data:
        warnings.append("Missing recommended field: updatedAt")
    
    # Update the result
    result["valid"] = len(errors) == 0
    result["errors"] = errors
    result["warnings"] = warnings
    result["stage"] = "enriched"
    
    return result


def validate_tagged_model(model_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a tagged model data file.
    
    Args:
        model_data: The model data to validate.
        
    Returns:
        Dictionary containing validation results.
    """
    # First validate as an enriched model
    result = validate_enriched_model(model_data)
    errors = result["errors"].copy()
    warnings = result["warnings"].copy()
    
    # Check tag fields
    if "tagIds" not in model_data:
        errors.append("Missing required field: tagIds")
    elif not isinstance(model_data["tagIds"], list):
        errors.append("Field 'tagIds' must be an array")
    else:
        for i, tag_id in enumerate(model_data["tagIds"]):
            if not isinstance(tag_id, int):
                errors.append(f"Tag ID at index {i} must be an integer")
    
    # Update the result
    result["valid"] = len(errors) == 0
    result["errors"] = errors
    result["warnings"] = warnings
    result["stage"] = "tagged"
    
    return result


def validate_api_model(model_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate an API-ready model data file.
    
    Args:
        model_data: The model data to validate.
        
    Returns:
        Dictionary containing validation results.
    """
    errors = []
    warnings = []
    
    # Check required API fields
    required_fields = ["modelId", "name", "displayName", "description", "tagIds"]
    for field in required_fields:
        if field not in model_data:
            errors.append(f"Missing required API field: {field}")
    
    # Check field types
    if "modelId" in model_data and not isinstance(model_data["modelId"], str):
        errors.append("Field 'modelId' must be a string")
    
    if "name" in model_data and not isinstance(model_data["name"], str):
        errors.append("Field 'name' must be a string")
    
    if "displayName" in model_data and not isinstance(model_data["displayName"], str):
        errors.append("Field 'displayName' must be a string")
    
    if "description" in model_data and not isinstance(model_data["description"], str):
        errors.append("Field 'description' must be a string")
    
    if "tagIds" in model_data:
        if not isinstance(model_data["tagIds"], list):
            errors.append("Field 'tagIds' must be an array")
        else:
            for i, tag_id in enumerate(model_data["tagIds"]):
                if not isinstance(tag_id, int):
                    errors.append(f"Tag ID at index {i} must be an integer")
    
    # Check for parameters
    if "parameters" in model_data and not isinstance(model_data["parameters"], str):
        errors.append("Field 'parameters' must be a string (serialized JSON)")
    
    # Check for version
    if "version" not in model_data:
        warnings.append("Missing recommended field: version")
    
    # Check for reference link
    if "referenceLink" not in model_data:
        warnings.append("Missing recommended field: referenceLink")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stage": "api"
    }


def detect_model_stage(model_data: Dict[str, Any]) -> str:
    """
    Detect the stage of a model data file.
    
    Args:
        model_data: The model data to detect the stage for.
        
    Returns:
        The detected stage ("raw", "enriched", "tagged", or "api").
    """
    # Check for API fields
    if all(field in model_data for field in ["displayName", "referenceLink"]):
        return "api"
    
    # Check for tagged fields
    if "tagIds" in model_data:
        return "tagged"
    
    # Check for enrichment fields
    if any(field in model_data for field in ["metadata", "createdAt", "updatedAt"]):
        return "enriched"
    
    # Default to raw
    return "raw"


def validate_model_file(file_path: Path, stage: str = "auto") -> Dict[str, Any]:
    """
    Validate a model data file.
    
    Args:
        file_path: Path to the model data file.
        stage: Pipeline stage to validate against ("raw", "enriched", "tagged", "api", or "auto").
        
    Returns:
        Dictionary containing validation results.
    """
    try:
        # Load model data
        with open(file_path, "r", encoding="utf-8") as f:
            model_data = json.load(f)
        
        # Detect stage if auto
        if stage == "auto":
            stage = detect_model_stage(model_data)
        
        # Validate based on stage
        if stage == "raw":
            result = validate_raw_model(model_data)
        elif stage == "enriched":
            result = validate_enriched_model(model_data)
        elif stage == "tagged":
            result = validate_tagged_model(model_data)
        elif stage == "api":
            result = validate_api_model(model_data)
        else:
            return {
                "valid": False,
                "errors": [f"Unknown stage: {stage}"],
                "warnings": [],
                "file": str(file_path)
            }
        
        # Add file path to result
        result["file"] = str(file_path)
        
        return result
        
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "errors": [f"Invalid JSON: {str(e)}"],
            "warnings": [],
            "file": str(file_path),
            "stage": stage
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": [],
            "file": str(file_path),
            "stage": stage
        }


def validate_directory(directory: Path, stage: str = "auto", recursive: bool = True) -> List[Dict[str, Any]]:
    """
    Validate all model data files in a directory.
    
    Args:
        directory: Path to the directory containing model data files.
        stage: Pipeline stage to validate against.
        recursive: Whether to validate files in subdirectories.
        
    Returns:
        List of dictionaries containing validation results for each file.
    """
    results = []
    
    # Get all JSON files
    pattern = "**/*.json" if recursive else "*.json"
    json_files = list(directory.glob(pattern))
    
    # Validate each file
    for file_path in json_files:
        result = validate_model_file(file_path, stage)
        results.append(result)
    
    return results


def main():
    """Main entry point for the validation script."""
    args = parse_args()
    
    # Configure logging
    log_level = "DEBUG" if args.verbose else None
    logger = get_logger("ValidateUtility", level=log_level)
    logger.info("Starting model validation")
    
    # Get input path
    input_path = Path(args.input_path)
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    # Validate input path
    if input_path.is_file():
        logger.info(f"Validating file: {input_path}")
        results = [validate_model_file(input_path, args.stage)]
    else:
        logger.info(f"Validating directory: {input_path}")
        results = validate_directory(input_path, args.stage)
    
    # Calculate summary
    valid_count = sum(1 for r in results if r["valid"])
    invalid_count = len(results) - valid_count
    error_count = sum(len(r["errors"]) for r in results)
    warning_count = sum(len(r["warnings"]) for r in results)
    
    # Print summary
    print(f"\nValidation Summary:")
    print(f"  Total files: {len(results)}")
    print(f"  Valid files: {valid_count}")
    print(f"  Invalid files: {invalid_count}")
    print(f"  Total errors: {error_count}")
    print(f"  Total warnings: {warning_count}")
    
    # Print detailed results if not summary only
    if not args.summary_only and invalid_count > 0:
        print("\nInvalid Files:")
        for result in results:
            if not result["valid"]:
                file_path = Path(result["file"]).name
                stage = result.get("stage", "unknown")
                print(f"  - {file_path} (Stage: {stage})")
                
                # Print errors
                for error in result["errors"]:
                    print(f"      Error: {error}")
                
                # Print warnings if verbose
                if args.verbose:
                    for warning in result["warnings"]:
                        print(f"      Warning: {warning}")
    
    # Write results to file if requested
    if args.output_file:
        output_path = Path(args.output_file)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({
                    "summary": {
                        "total": len(results),
                        "valid": valid_count,
                        "invalid": invalid_count,
                        "errors": error_count,
                        "warnings": warning_count
                    },
                    "results": results
                }, f, indent=2)
            
            logger.info(f"Validation results written to {output_path}")
            print(f"\nValidation results written to {output_path}")
        except Exception as e:
            logger.error(f"Error writing validation results: {e}")
            print(f"Error writing validation results: {e}")
    
    # Exit with appropriate code
    sys.exit(0 if invalid_count == 0 else 1)


if __name__ == "__main__":
    main()
