# AI Model Seeding Pipeline

A robust, extensible pipeline for extracting, enriching, and seeding AI model data to a target API.

## Architecture

This project follows SOLID principles and implements a modular pipeline architecture with the following components:

1. **Extractor**: Extracts model data from various sources (Ollama API, JSON files)
2. **Enricher**: Enriches model data with additional metadata
3. **TagMapper**: Maps tags to models based on configurable rules
4. **ModelMapper**: Maps enriched model data to the API schema
5. **Seeder**: Seeds models to the target API
6. **Archiver**: Archives processed files to prevent reprocessing

## Project Structure

```
.
├── pipeline/               # Core pipeline components
│   ├── __init__.py
│   ├── archiver.py         # Archiver component implementations
│   ├── base.py             # Base classes with shared functionality
│   ├── config.py           # Configuration management
│   ├── enricher.py         # Enricher component implementations
│   ├── extractor.py        # Extractor component implementations
│   ├── factory.py          # Factory for creating pipeline components
│   ├── interfaces.py       # Core interfaces defining contracts
│   ├── logger.py           # Logging implementation
│   ├── model_mapper.py     # Model mapper component implementations
│   ├── pipeline.py         # Pipeline orchestrator
│   ├── seeder.py           # Seeder component implementations
│   └── tag_mapper.py       # Tag mapper component implementations
├── data/                   # Data directories
│   ├── enriched/           # Enriched model data
│   ├── mapped/             # API-ready model data
│   ├── processed/          # Tagged model data
│   └── raw/                # Raw extracted model data
├── archive/                # Archived files
├── logs/                   # Log files
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Shared test fixtures
│   ├── test_archiver.py
│   ├── test_enricher.py
│   ├── test_extractor.py
│   ├── test_model_mapper.py
│   ├── test_pipeline.py
│   ├── test_seeder.py
│   └── test_tag_mapper.py
├── .env                    # Environment variables (not in version control)
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore file
├── requirements.txt        # Project dependencies
└── run_pipeline.py         # Main entry point script
```

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure as needed

## Configuration

The pipeline is configured through environment variables, which can be set in the `.env` file.

Key configuration options:
- **Directory paths**: Configure where data is stored at each pipeline stage
- **API settings**: Configure API endpoints and authentication
- **Component defaults**: Set which component implementations to use
- **Logging**: Configure log levels and output locations

## Usage

Run the pipeline using the `run_pipeline.py` script:

```
python run_pipeline.py
```

### Command Line Arguments

```
# Run the complete pipeline
python run_pipeline.py

# Run with specific component implementations
python run_pipeline.py --extractor ollama --enricher metadata --seeder api

# Run only a specific phase
python run_pipeline.py --phase extract

# Dry run (validate pipeline but don't execute)
python run_pipeline.py --dry-run

# Use a custom configuration file
python run_pipeline.py --config my_config.json

# Enable verbose logging
python run_pipeline.py --verbose
```

## Example

```python
from pipeline.factory import PipelineFactory
from pipeline.config import get_config

# Create a pipeline with default components
factory = PipelineFactory()
pipeline = factory.create_pipeline()

# Run the pipeline
result = pipeline.run({})

if result["success"]:
    print("Pipeline executed successfully!")
else:
    print(f"Pipeline failed: {result['error']['message']}")
```

## Extending the Pipeline

To add a new component implementation:

1. Create a new class that inherits from the appropriate base class
2. Implement the required methods
3. Register it in the factory

Example:

```python
from pipeline.enricher import BaseEnricher

class MyCustomEnricher(BaseEnricher):
    def enrich_model(self, model_data):
        # Custom enrichment logic
        model_data["custom_field"] = "custom value"
        return model_data
```

## License

[MIT License](LICENSE)
