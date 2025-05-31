# AI Model Seeding Pipeline: CLI User Guide

This guide provides comprehensive instructions for using the AI Model Seeding Pipeline CLI tools to extract, process, and seed AI model data to your API.

## Table of Contents

1. [Pipeline Overview](#pipeline-overview)
2. [Setup and Configuration](#setup-and-configuration)
3. [CLI Tools Reference](#cli-tools-reference)
   - [Extraction](#extraction-extractpy)
   - [Enrichment](#enrichment-enrichpy)
   - [Tag Mapping](#tag-mapping-map_tagspy)
   - [Model Mapping](#model-mapping-map_modelspy)
   - [Seeding](#seeding-seedpy)
   - [Archiving](#archiving-archivepy)
4. [Utility Tools](#utility-tools)
   - [Status Checking](#status-checking-statuspy)
   - [Cleanup](#cleanup-cleanuppy)
   - [Validation](#validation-validatepy)
5. [Complete Pipeline](#complete-pipeline-run_pipelinepy)
6. [Examples and Workflows](#examples-and-workflows)
7. [Troubleshooting](#troubleshooting)

## Pipeline Overview

The AI Model Seeding Pipeline is designed to extract AI model data from various sources, process it through several stages, and seed it to a target API. The pipeline consists of these main stages:

1. **Extraction**: Pull model data from sources like Ollama API
2. **Enrichment**: Add metadata and enhance model information
3. **Tag Mapping**: Convert tag names to tag IDs
4. **Model Mapping**: Transform models to API schema
5. **Seeding**: Send models to the target API
6. **Archiving**: Store processed files

## Setup and Configuration

### Prerequisites

- Python 3.7+
- Required packages installed via `pip install -r requirements.txt`
- Access to model sources (e.g., Ollama API)
- Target API endpoint (optional for testing)

### Configuration (.env file)

The pipeline is configured through environment variables in a `.env` file. Create this file in the project root with the following settings:

```ini
# Directories
DATA_DIR=./data
RAW_DATA_DIR=./data/raw
ENRICHED_DATA_DIR=./data/enriched
PROCESSED_DATA_DIR=./data/processed
MAPPED_DATA_DIR=./data/mapped
ARCHIVE_DIR=./archive
TAGS_DIR=./Tags

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/pipeline.log
CONSOLE_LOG=true
FILE_LOG=true

# API Settings
API_URL=http://your-api-endpoint/api
API_KEY=your_api_key_here
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3

# Component Types
DEFAULT_EXTRACTOR_TYPE=ollama
DEFAULT_ENRICHER_TYPE=metadata
DEFAULT_TAG_MAPPER_TYPE=simple
DEFAULT_MODEL_MAPPER_TYPE=standard
DEFAULT_SEEDER_TYPE=api
DEFAULT_ARCHIVER_TYPE=metadata
```

## CLI Tools Reference

### Extraction (`extract.py`)

Extracts model data from sources like Ollama API or JSON files.

```bash
# Extract from Ollama API
python scripts/extract.py --source-type ollama --output-dir ./data/raw

# Extract from JSON files
python scripts/extract.py --source-type json --input-dir ./input --output-dir ./data/raw

# Options
python scripts/extract.py --help
```

Key parameters:
- `--source-type`: Type of source to extract from (`ollama` or `json`)
- `--output-dir`: Directory to save extracted model data
- `--ollama-url`: URL for Ollama API (for Ollama extraction)
- `--input-dir`: Input directory containing JSON files (for JSON extraction)
- `--verbose`: Enable verbose logging

### Enrichment (`enrich.py`)

Enriches model data with additional metadata.

```bash
# Basic enrichment
python scripts/enrich.py --input-dir ./data/raw --output-dir ./data/enriched

# Using HuggingFace enricher
python scripts/enrich.py --enricher-type huggingface --input-dir ./data/raw --output-dir ./data/enriched

# Options
python scripts/enrich.py --help
```

Key parameters:
- `--input-dir`: Directory containing raw model data files
- `--output-dir`: Directory to save enriched model data
- `--enricher-type`: Type of enricher to use (`metadata` or `huggingface`)
- `--hf-api-key`: HuggingFace API key (for HuggingFace enricher)
- `--verbose`: Enable verbose logging

### Tag Mapping (`map_tags.py`)

Maps tag names to tag IDs based on a mapping file.

```bash
# Basic tag mapping
python scripts/map_tags.py --input-dir ./data/enriched --output-dir ./data/processed

# Auto-create missing tags
python scripts/map_tags.py --input-dir ./data/enriched --output-dir ./data/processed --auto-create

# Options
python scripts/map_tags.py --help
```

Key parameters:
- `--input-dir`: Directory containing enriched model data files
- `--output-dir`: Directory to save tagged model data
- `--tag-mapper-type`: Type of tag mapper to use (`simple` or `fallback`)
- `--tag-map-file`: Path to tag mapping file
- `--auto-create`: Automatically create tags that don't exist in the mapping
- `--verbose`: Enable verbose logging

### Model Mapping (`map_models.py`)

Maps models to the API schema format.

```bash
# Basic model mapping
python scripts/map_models.py --input-dir ./data/processed --output-dir ./data/mapped

# With schema validation
python scripts/map_models.py --input-dir ./data/processed --output-dir ./data/mapped --validate-schema

# Options
python scripts/map_models.py --help
```

Key parameters:
- `--input-dir`: Directory containing tagged model data files
- `--output-dir`: Directory to save API-ready model data
- `--model-mapper-type`: Type of model mapper to use (`standard`)
- `--validate-schema`: Validate models against API schema
- `--reference-url-prefix`: Prefix for reference URLs in mapped models
- `--verbose`: Enable verbose logging

### Seeding (`seed.py`)

Seeds models to the target API.

```bash
# Seed to real API
python scripts/seed.py --input-dir ./data/mapped --api-url http://your-api-endpoint/api --api-key your_api_key

# Dry run (no actual API calls)
python scripts/seed.py --input-dir ./data/mapped --dry-run

# Options
python scripts/seed.py --help
```

Key parameters:
- `--input-dir`: Directory containing API-ready model data files
- `--api-url`: URL for the API endpoint
- `--api-key`: API key for authentication
- `--seeder-type`: Type of seeder to use (`api` or `mock`)
- `--batch-size`: Number of models to seed in each batch
- `--delay`: Delay between API calls in seconds
- `--retry-attempts`: Number of retry attempts for failed API calls
- `--timeout`: Timeout for API calls in seconds
- `--dry-run`: Validate but don't actually send to API
- `--verbose`: Enable verbose logging

### Archiving (`archive.py`)

Archives processed files to the archive directory.

```bash
# Basic archiving
python scripts/archive.py --input-dir ./data/mapped --archive-dir ./archive

# Organized by date with timestamps
python scripts/archive.py --input-dir ./data/mapped --archive-dir ./archive --archiver-type organized --organize-by-date --include-timestamp

# Options
python scripts/archive.py --help
```

Key parameters:
- `--input-dir`: Directory containing files to archive
- `--archive-dir`: Directory to move archived files to
- `--archiver-type`: Type of archiver to use (`simple`, `organized`, or `metadata`)
- `--organize-by-date`: Organize archived files by date (for organized archiver)
- `--include-timestamp`: Include timestamp in archived file names
- `--pattern`: Glob pattern to filter files for archiving
- `--verbose`: Enable verbose logging

## Utility Tools

### Status Checking (`status.py`)

Checks the status of the pipeline, including file counts and directory statistics.

```bash
# Basic status check
python scripts/status.py

# Detailed status with latest files
python scripts/status.py --detailed --show-latest 5

# Output as JSON
python scripts/status.py --json --output-file status.json

# Options
python scripts/status.py --help
```

Key parameters:
- `--detailed`: Show detailed status information
- `--show-latest`: Number of latest models to show for each stage
- `--output-file`: File to write status to (JSON format)
- `--json`: Output in JSON format
- `--verbose`: Enable verbose logging

### Cleanup (`cleanup.py`)

Cleans up temporary files and directories.

```bash
# Clean all pipeline directories
python scripts/cleanup.py --all

# Clean specific directories
python scripts/cleanup.py --raw --enriched --logs

# Force cleanup without confirmation
python scripts/cleanup.py --all --force

# Options
python scripts/cleanup.py --help
```

Key parameters:
- `--all`: Clean all pipeline directories
- `--raw`: Clean raw data directory
- `--enriched`: Clean enriched data directory
- `--processed`: Clean processed data directory
- `--mapped`: Clean API-mapped data directory
- `--logs`: Clean log files
- `--force`: Force cleanup without confirmation
- `--verbose`: Enable verbose logging

### Validation (`validate.py`)

Validates model data files against expected schemas.

```bash
# Validate files in a directory
python scripts/validate.py ./data/mapped

# Validate specific file with stage detection
python scripts/validate.py ./data/mapped/model.json --stage auto

# Output validation results to file
python scripts/validate.py ./data/mapped --output-file validation.json

# Options
python scripts/validate.py --help
```

Key parameters:
- `input_path`: Directory or file to validate
- `--stage`: Pipeline stage to validate against (`raw`, `enriched`, `tagged`, `api`, or `auto`)
- `--output-file`: File to write validation results to (JSON format)
- `--summary-only`: Only output a summary of validation results
- `--verbose`: Enable verbose logging

## Complete Pipeline (`run_pipeline.py`)

Runs the complete pipeline from extraction to archiving.

```bash
# Run the complete pipeline
python run_pipeline.py

# Run with specific component types
python run_pipeline.py --extractor ollama --enricher metadata --seeder mock

# Run only a specific phase
python run_pipeline.py --phase extract

# Options
python run_pipeline.py --help
```

Key parameters:
- `--config`: Path to a JSON configuration file
- `--extractor`: Type of extractor to use
- `--enricher`: Type of enricher to use
- `--tag-mapper`: Type of tag mapper to use
- `--model-mapper`: Type of model mapper to use
- `--seeder`: Type of seeder to use
- `--archiver`: Type of archiver to use
- `--source-config`: Path to a JSON file with source configuration
- `--phase`: Run only the specified phase
- `--dry-run`: Validate the pipeline but don't execute it
- `--verbose`: Enable verbose logging

## Examples and Workflows

### Full Pipeline Workflow

To run the complete pipeline from start to finish:

```bash
# Full pipeline
python run_pipeline.py

# Full pipeline with verbose logging
python run_pipeline.py --verbose
```

### Step-by-Step Workflow

To run each step manually:

```bash
# Step 1: Extract models from Ollama
python scripts/extract.py --source-type ollama

# Step 2: Enrich the extracted models
python scripts/enrich.py

# Step 3: Map tags to tag IDs
python scripts/map_tags.py

# Step 4: Map models to API schema
python scripts/map_models.py

# Step 5: Seed models to API (dry run)
python scripts/seed.py --dry-run

# Step 6: Archive processed files
python scripts/archive.py
```

### Testing and Development Workflow

For testing and development:

```bash
# Extract a small sample
python scripts/extract.py --source-type ollama --limit 3

# Process with mock components
python run_pipeline.py --seeder mock --dry-run
```

## Troubleshooting

### Common Issues

1. **Missing Configuration**
   - Ensure you have a `.env` file in the project root
   - Check that all required directories exist

2. **API Connection Issues**
   - Verify API URL and API key in `.env`
   - Try with `--dry-run` to test the pipeline without API calls

3. **File Processing Errors**
   - Use `validate.py` to check file formats
   - Check log files in the `logs` directory for detailed error messages

4. **Performance Issues**
   - Adjust batch sizes in `.env` for extraction and seeding
   - Use `--parallel` options where available for parallel processing

### Logging

Logs are stored in the location specified by `LOG_FILE` in your `.env` file (default: `./logs/pipeline.log`). Use these logs for debugging and troubleshooting.

To enable verbose logging for any command, add the `--verbose` flag:

```bash
python scripts/extract.py --verbose
```