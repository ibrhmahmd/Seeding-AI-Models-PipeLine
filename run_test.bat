@echo off
REM Test script for running the AI Model Seeding Pipeline with environment variables

REM Set environment variables for directories
SET DATA_DIR=e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\data
SET RAW_DATA_DIR=e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\data\raw
SET ENRICHED_DATA_DIR=e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\data\enriched
SET PROCESSED_DATA_DIR=e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\data\processed
SET MAPPED_DATA_DIR=e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\data\mapped
SET ARCHIVE_DIR=e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\archive
SET TAGS_DIR=e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\Tags

REM Set Logging environment variables
SET LOG_LEVEL=INFO
SET LOG_FILE=e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\logs\pipeline.log
SET CONSOLE_LOG=true
SET FILE_LOG=true

REM Set API environment variables
REM Update these with your actual API settings
SET OLLAMA_API_URL=http://localhost:11434
SET API_URL=http://ollamanetgateway.runasp.net/admin/AIModelOperations
SET API_KEY=your_api_key_here
SET API_TIMEOUT=30
SET API_RETRY_ATTEMPTS=3

REM Set component type defaults
SET DEFAULT_EXTRACTOR_TYPE=ollama
SET DEFAULT_ENRICHER_TYPE=metadata
SET DEFAULT_TAG_MAPPER_TYPE=simple
SET DEFAULT_MODEL_MAPPER_TYPE=standard
SET DEFAULT_SEEDER_TYPE=mock
SET DEFAULT_ARCHIVER_TYPE=metadata

REM Create necessary directories
mkdir "%DATA_DIR%" 2>nul
mkdir "%RAW_DATA_DIR%" 2>nul
mkdir "%ENRICHED_DATA_DIR%" 2>nul
mkdir "%PROCESSED_DATA_DIR%" 2>nul
mkdir "%MAPPED_DATA_DIR%" 2>nul
mkdir "%ARCHIVE_DIR%" 2>nul
mkdir "%TAGS_DIR%" 2>nul
mkdir "e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\logs" 2>nul

REM Choose which test to run
echo Available tests:
echo 1. Extract from Ollama
echo 2. Enrich raw data
echo 3. Map tags
echo 4. Map models
echo 5. Seed (mock mode)
echo 6. Archive
echo 7. Complete pipeline (mock seeder)
echo.

echo Choose a test to run:
echo 1 - Extract from Ollama
echo 2 - Enrich raw data
echo 3 - Map tags
echo 4 - Map models
echo 5 - Seed (mock mode)
echo 6 - Archive
echo 7 - Complete pipeline (mock seeder)
echo.

choice /C 1234567 /N /M "Enter test number (1-7): "
set test_num=%ERRORLEVEL%

if %test_num%==1 (
    echo Running extraction test...
    python "e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\scripts\extract.py" --source-type ollama --verbose
) else if %test_num%==2 (
    echo Running enrichment test...
    python "e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\scripts\enrich.py" --input-dir "%RAW_DATA_DIR%" --output-dir "%ENRICHED_DATA_DIR%" --verbose
) else if %test_num%==3 (
    echo Running tag mapping test...
    python "e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\scripts\map_tags.py" --input-dir "%ENRICHED_DATA_DIR%" --output-dir "%PROCESSED_DATA_DIR%" --verbose
) else if %test_num%==4 (
    echo Running model mapping test...
    python "e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\scripts\map_models.py" --input-dir "%PROCESSED_DATA_DIR%" --output-dir "%MAPPED_DATA_DIR%" --verbose
) else if %test_num%==5 (
    echo Running seeding test (mock mode)...
    python "e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\scripts\seed.py" --input-dir "%MAPPED_DATA_DIR%" --seeder-type mock --dry-run --verbose
) else if %test_num%==6 (
    echo Running archiving test...
    python "e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\scripts\archive.py" --input-dir "%MAPPED_DATA_DIR%" --archive-dir "%ARCHIVE_DIR%" --verbose
) else if %test_num%==7 (
    echo Running complete pipeline with mock seeder...
    python "e:\Users\ibrahim\Downloads\Seeding Database with AI Models and Entities\run_pipeline.py" --seeder mock --verbose
) else (
    echo Invalid selection
)

echo.
echo Test completed. Check the logs for details.
pause
