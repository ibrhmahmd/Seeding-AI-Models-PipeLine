"""
Pytest configuration for the AI Model Seeding Pipeline tests.

This module contains fixtures and configuration for pytest.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any

import pytest

# Define project root
@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.absolute()

# Define test data directory
@pytest.fixture
def test_data_dir(project_root: Path) -> Path:
    """Get the test data directory."""
    data_dir = project_root / "tests" / "fixtures" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

# Define test output directory
@pytest.fixture
def test_output_dir(project_root: Path) -> Path:
    """
    Create and get a clean test output directory.
    
    This directory is cleaned before each test.
    """
    output_dir = project_root / "tests" / "output"
    
    # Clean directory if it exists
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    # Create directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir

# Define test model fixture
@pytest.fixture
def test_model() -> Dict[str, Any]:
    """Get a test model dictionary."""
    return {
        "name": "test-model",
        "modelId": "test-model-123",
        "description": "Test model for unit tests",
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "tags": ["test", "model", "unit-test"]
    }

# Define test tagged model fixture
@pytest.fixture
def test_tagged_model(test_model: Dict[str, Any]) -> Dict[str, Any]:
    """Get a test model with mapped tag IDs."""
    model = test_model.copy()
    model["tagIds"] = [1, 2, 3]
    return model

# Define test API model fixture
@pytest.fixture
def test_api_model(test_tagged_model: Dict[str, Any]) -> Dict[str, Any]:
    """Get a test model mapped to API schema."""
    return {
        "modelId": test_tagged_model["modelId"],
        "name": test_tagged_model["name"],
        "displayName": test_tagged_model["name"].replace("-", " ").title(),
        "description": test_tagged_model["description"],
        "parameters": json.dumps(test_tagged_model["parameters"]),
        "tagIds": test_tagged_model["tagIds"],
        "referenceLink": "https://example.com/models/test-model",
        "isActive": True,
        "version": "1.0"
    }

# Create test model file
@pytest.fixture
def test_model_file(test_data_dir: Path, test_model: Dict[str, Any]) -> Path:
    """Create and get a test model file."""
    file_path = test_data_dir / "test_model.json"
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(test_model, f, indent=2)
    
    return file_path

# Create test tag map
@pytest.fixture
def test_tag_map() -> Dict[str, int]:
    """Get a test tag map dictionary."""
    return {
        "test": 1,
        "model": 2,
        "unit-test": 3,
        "ai": 4,
        "language": 5
    }

# Create test tag map file
@pytest.fixture
def test_tag_map_file(test_data_dir: Path, test_tag_map: Dict[str, int]) -> Path:
    """Create and get a test tag map file."""
    file_path = test_data_dir / "test_tag_map.json"
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(test_tag_map, f, indent=2)
    
    return file_path
