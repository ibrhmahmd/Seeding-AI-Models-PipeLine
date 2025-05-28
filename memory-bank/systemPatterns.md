# System Patterns

## System Architecture
- Modular Python scripts for data extraction, transformation, and management
- JSON files as the primary data interchange and storage format
- Directory structure separates models, tags, scripts, and logs

## Key Technical Decisions
- Use of Python for scripting due to its ecosystem and flexibility
- JSON for human-readable, extensible data storage
- Logging and versioning of data operations

## Design Patterns
- ETL (Extract, Transform, Load) for model/entity data
- Script modularity: each script has a focused responsibility (e.g., extraction, sorting, mapping)
- Separation of data (JSON) and logic (Python scripts)

## Component Relationships
- Scripts operate on and produce JSON data files
- Model/tag directories organize raw and processed data
- Logs track seeding and transformation operations 