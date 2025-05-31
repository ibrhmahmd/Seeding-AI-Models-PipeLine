# Phase 4: CLI Scripts & Integration

## Objectives
- Create thin CLI wrappers for the pipeline
- Ensure backward compatibility with existing workflows
- Provide command-line utilities for common tasks

## Tasks

### 1. Command Line Interface
- [ ] Create CLI wrappers in the `/scripts/` directory:
  - [ ] `extract.py` - Extract data from sources
  - [ ] `enrich.py` - Enrich extracted model data
  - [ ] `map_tags.py` - Map tags to models
  - [ ] `map_models.py` - Map to API schema
  - [ ] `seed.py` - Seed models to API
  - [ ] `run_pipeline.py` - Run the full pipeline

### 2. Argument Parsing
- [ ] Implement consistent argument parsing across all scripts
- [ ] Support both individual component options and pipeline options
- [ ] Add help text and documentation for all command-line options
- [ ] Ensure sensible defaults for all parameters

### 3. Backward Compatibility
- [ ] Create adapters for existing script interfaces
- [ ] Ensure new CLI maintains same input/output patterns as old scripts
- [ ] Document migration path from old scripts to new system
- [ ] Add deprecation warnings for old usage patterns

### 4. Utilities
- [ ] Create helper scripts for common tasks:
  - [ ] `cleanup.py` - Clean up temporary files
  - [ ] `validate.py` - Validate data files
  - [ ] `status.py` - Check pipeline status
  - [ ] `archive_manager.py` - Manage archived files

### 5. Documentation
- [ ] Generate CLI usage documentation
- [ ] Create example commands for common scenarios
- [ ] Add inline help text for all scripts
- [ ] Document environment variables and configuration options

## Expected Outcomes
- Complete set of CLI scripts for all pipeline functions
- Backward compatibility with existing workflows
- Clear documentation for all command-line tools
- Utility scripts for common maintenance tasks

## Next Phase
After completing the CLI scripts and integration, proceed to Phase 5: Testing & Validation.
