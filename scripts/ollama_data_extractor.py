import json
import subprocess
import os
import re
from datetime import datetime
import requests

# Configuration
TAG_IDS_FILE = "Tags/created_tag_ids.json"
OUTPUT_DIR = "data/processed"
MISSING_TAGS_FILE = "newly_missing_tags.txt"
RAW_OUTPUT_DIR = "data/raw"

# Helper function to load tag IDs
def load_tag_ids():
    if not os.path.exists(TAG_IDS_FILE):
        print(f"Warning: Tag IDs file not found at {TAG_IDS_FILE}")
        return {}
    try:
        with open(TAG_IDS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {TAG_IDS_FILE}")
        return {}

# Helper function to safely get nested dictionary values
def get_nested(data, keys, default=None):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return default
    return data if data is not None else default

# Helper function to derive tags from data
def derive_tags(data, tag_ids_map):
    derived_tags = []
    missing_tags = set()

    # Family
    family = get_nested(data, ["details", "family"])
    if family:
        family_tag = f"{family.capitalize()} Family"
        if family_tag in tag_ids_map:
            derived_tags.append({"tagId": tag_ids_map[family_tag]})
        else:
            missing_tags.add(family_tag)

    # Parameter Size
    param_size = get_nested(data, ["details", "parameter_size"])
    if param_size:
        size_tag = f"{param_size} Parameters"
        if size_tag in tag_ids_map:
            derived_tags.append({"tagId": tag_ids_map[size_tag]})
        else:
            missing_tags.add(size_tag)

    # Quantization Level
    quant_level = get_nested(data, ["details", "quantization_level"])
    if quant_level:
        if quant_level in tag_ids_map:
            derived_tags.append({"tagId": tag_ids_map[quant_level]})
        else:
            missing_tags.add(quant_level)

    # Capabilities (e.g., completion, tools)
    capabilities = get_nested(data, ["details", "capabilities"], default=[])
    for cap in capabilities:
        cap_tag = cap.capitalize()
        if cap_tag == "Tools":
            cap_tag = "Function Calling" # Map specific capability names if needed
        if cap_tag in tag_ids_map:
            derived_tags.append({"tagId": tag_ids_map[cap_tag]})
        else:
            missing_tags.add(cap_tag)

    # Add other relevant tags based on analysis (e.g., architecture, license type)
    # Example: Architecture
    arch = get_nested(data, ["details", "model_info", "general.architecture"])
    if arch:
        arch_tag = arch.capitalize()
        if arch_tag in tag_ids_map:
            derived_tags.append({"tagId": tag_ids_map[arch_tag]})
        else:
            missing_tags.add(arch_tag)

    # Example: License (extracting a simple name might be complex)
    # For now, let's assume a tag like "Llama 3 License" exists if family is llama
    if family and family.lower() == "llama":
        license_tag = "Llama 3 License" # This needs refinement based on actual license content
        if license_tag in tag_ids_map:
            derived_tags.append({"tagId": tag_ids_map[license_tag]})
        else:
            missing_tags.add(license_tag)

    return derived_tags, list(missing_tags)

# Function to get list of installed models
def get_installed_models():
    # Try CLI first
    try:
        result = subprocess.run(["ollama", "ls"], capture_output=True, text=True, check=True, timeout=30)
        models = []
        for line in result.stdout.splitlines():
            if line.strip() and not line.startswith("NAME") and not line.startswith("-"):
                # Split by whitespace, first column is the model name
                model_name = line.split()[0]
                models.append(model_name)
        print(f"Found models via CLI: {models}")
        if models:
            return models
    except Exception as e:
        print(f"CLI 'ollama ls' failed: {e}. Trying API fallback...")
    # Try API fallback
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        print(f"Found models via API: {models}")
        return models
    except Exception as api_e:
        print(f"API fallback for model list failed: {api_e}")
        return []

# Function to get model info (CLI or API fallback)
def get_model_info(model_name):
    # Try CLI first
    try:
        result = subprocess.run(["ollama", "show", "--json", model_name], capture_output=True, text=True, check=True, timeout=60)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"CLI failed for {model_name}: {e}. Trying API fallback...")
        # Try API fallback
        try:
            resp = requests.post("http://localhost:11434/api/show", json={"name": model_name}, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as api_e:
            print(f"API fallback failed for {model_name}: {api_e}")
            return None

# Main function to process a model
def process_model(model_name):
    print(f"Processing model: {model_name}")
    tag_ids_map = load_tag_ids()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(RAW_OUTPUT_DIR, exist_ok=True)
    ollama_data = get_model_info(model_name)
    if ollama_data is None:
        print(f"Failed to get data for {model_name}")
        return
    # Save raw Ollama JSON
    raw_output_filename = os.path.join(RAW_OUTPUT_DIR, f"{model_name.replace(':', '_').replace('/', '_')}_raw.json")
    try:
        with open(raw_output_filename, "w") as f:
            json.dump(ollama_data, f, indent=2)
        print(f"Saved raw Ollama JSON for {model_name} at {raw_output_filename}")
    except IOError as e:
        print(f"Error writing raw Ollama JSON file {raw_output_filename}: {e}")
    # --- Data Mapping --- (Based on revised_strategy.md)
    api_payload = {}

    # Basic Info
    api_payload["name"] = model_name
    api_payload["description"] = f"Details for {model_name}. Description to be added." # Placeholder
    version_match = re.search(r":(.*?)$", model_name)
    api_payload["version"] = version_match.group(1) if version_match else "latest"
    api_payload["size"] = get_nested(ollama_data, ["details", "size"])

    # Dates and Links (Placeholders/Defaults)
    modified_at_str = get_nested(ollama_data, ["modified_at"])
    try:
        # Ollama format: 2025-04-29T16:41:07.6451864+03:00
        # Target format: 2025-05-14T18:38:09.805Z
        if modified_at_str:
            dt_obj = datetime.fromisoformat(modified_at_str)
            api_payload["releasedAt"] = dt_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            api_payload["releasedAt"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ") # Default to now
    except ValueError:
         api_payload["releasedAt"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ") # Default on parse error

    api_payload["referenceLink"] = get_nested(ollama_data, ["details", "project_url"], "#") # Placeholder
    api_payload["imageUrl"] = "#" # Placeholder
    api_payload["fromOllama"] = False

    # Details from Ollama JSON
    api_payload["license"] = str(get_nested(ollama_data, ["license"], ""))[:255] # Truncate if needed
    api_payload["template"] = get_nested(ollama_data, ["template"], "")
    api_payload["modelFile"] = get_nested(ollama_data, ["modelfile"], "")
    api_payload["digest"] = get_nested(ollama_data, ["details", "digest"])
    api_payload["format"] = get_nested(ollama_data, ["details", "format"])
    api_payload["parameterSize"] = get_nested(ollama_data, ["details", "parameter_size"])
    api_payload["quantizationLevel"] = get_nested(ollama_data, ["details", "quantization_level"])
    api_payload["parentModel"] = get_nested(ollama_data, ["details", "parent_model"])
    api_payload["family"] = get_nested(ollama_data, ["details", "family"])
    api_payload["families"] = get_nested(ollama_data, ["details", "families"], [])
    api_payload["languages"] = [] # Placeholder - requires external sourcing

    # Details from model_info
    api_payload["architecture"] = get_nested(ollama_data, ["details", "model_info", "general.architecture"])
    try:
        api_payload["fileType"] = int(get_nested(ollama_data, ["details", "model_info", "general.file_type"], 0))
    except (ValueError, TypeError):
        api_payload["fileType"] = 0
    try:
        api_payload["parameterCount"] = int(get_nested(ollama_data, ["details", "model_info", "general.parameter_count"], 0))
    except (ValueError, TypeError):
        api_payload["parameterCount"] = 0
    try:
        api_payload["quantizationVersion"] = int(get_nested(ollama_data, ["details", "model_info", "general.quantization_version"], 0))
    except (ValueError, TypeError):
        api_payload["quantizationVersion"] = 0

    # Derived fields
    api_payload["sizeLabel"] = api_payload["parameterSize"] if api_payload["parameterSize"] else "Unknown"
    # Basic model type derivation - needs refinement
    if "vision" in api_payload["family"].lower() if api_payload["family"] else False:
        api_payload["modelType"] = "Multimodal"
    else:
        api_payload["modelType"] = "Language Model"

    # Tags
    derived_tags, missing_tags = derive_tags(ollama_data, tag_ids_map)
    api_payload["tags"] = derived_tags

    if missing_tags:
        print(f"Warning: Missing Tag IDs for model {model_name}: {missing_tags}")
        # Optionally, write missing tags to a file for later creation
        with open(MISSING_TAGS_FILE, "a") as f:
            f.write(f"Model: {model_name}\n")
            for tag in missing_tags:
                f.write(f"- {tag}\n")
            f.write("\n")

    # Save processed/mapped payload
    output_filename = os.path.join(OUTPUT_DIR, f"{model_name.replace(':', '_').replace('/', '_')}.json")
    try:
        with open(output_filename, "w") as f:
            json.dump(api_payload, f, indent=2)
        print(f"Successfully generated payload for {model_name} at {output_filename}")
    except IOError as e:
        print(f"Error writing payload file {output_filename}: {e}")
    except TypeError as e:
        print(f"Error serializing payload for {model_name}: {e}")
        print(f"Payload sample: {str(api_payload)[:500]}...")

# --- Example Usage --- 
if __name__ == "__main__":
    # Clear missing tags file at the start
    if os.path.exists(MISSING_TAGS_FILE):
        os.remove(MISSING_TAGS_FILE)

    models = get_installed_models()
    print(f"DEBUG: Models found for processing: {models}")
    if not models:
        print("No models found to process.")
    for model in models:
        print(f"DEBUG: Starting processing for model: {model}")
        try:
            process_model(model)
        except Exception as e:
            print(f"ERROR: Exception while processing {model}: {e}")
    print("All models processed.")

