import json
import os
from datetime import datetime
import glob

def map_model_to_api_schema(model_data_path, tags_data_path, output_dir):
    try:
        with open(model_data_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Model data file not found: {model_data_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {model_data_path}")
        return None

    try:
        with open(tags_data_path, 'r') as f:
            tag_map = json.load(f)
    except FileNotFoundError:
        print(f"Error: Tags data file not found: {tags_data_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {tags_data_path}")
        return None

    # --- Field Mapping ---
    api_payload = {}

    # Use the first variant's name as the primary identifier
    primary_variant_name = data.get("variants", [{}])[0].get("name", data.get("name"))
    api_payload["name"] = primary_variant_name

    api_payload["description"] = data.get("full_description", data.get("short_description", "No description available."))

    # Extract version from the primary variant name (e.g., 'latest' from 'devstral:latest')
    version = primary_variant_name.split(':')[-1] if ':' in primary_variant_name else 'latest'
    api_payload["version"] = version

    api_payload["size"] = data.get("variants", [{}])[0].get("size_gb", "Unknown")

    # Use updated_at_iso as release date (approximation)
    # Add note about approximation later if needed
    release_date_str = data.get("updated_at_iso", datetime.now().isoformat())
    # Ensure it's in the correct format Z at the end
    if not release_date_str.endswith('Z'):
         release_date_str += 'Z'
    api_payload["releasedAt"] = release_date_str # "2025-05-14T18:38:09.805Z"

    api_payload["referenceLink"] = data.get("source_huggingface_page", data.get("source_ollama_page", ""))

    # Attempt to get a better image URL if available
    api_payload["imageUrl"] = data.get("image_url", "https://huggingface.co/mistralai/resolve/main/logo.png") # Defaulting to Mistral logo for devstral

    api_payload["fromOllama"] = False # User requirement

    api_payload["license"] = data.get("license", "Unknown")

    # Fields often missing from scraping
    api_payload["template"] = data.get("template", None)
    api_payload["modelFile"] = data.get("modelFile", None)
    api_payload["digest"] = data.get("digest", None)
    api_payload["format"] = data.get("format", None)
    api_payload["quantizationLevel"] = data.get("quantizationLevel", None)
    api_payload["quantizationVersion"] = data.get("quantizationVersion", 0) # Default to 0 if missing
    api_payload["fileType"] = data.get("fileType", 0) # Default to 0 if missing

    api_payload["parameterSize"] = data.get("parameter_size_label", "Unknown")
    api_payload["parentModel"] = data.get("parent_model_hf", None)
    api_payload["family"] = data.get("author", data.get("name").split(':')[0]).replace(" AI", "") # Infer family
    api_payload["families"] = [api_payload["family"]] if api_payload["family"] else []

    # Clean up language data
    languages_raw = data.get("languages_hf", [])
    languages_cleaned = []
    if languages_raw and isinstance(languages_raw, list) and "Multiple" in languages_raw[0]:
        languages_cleaned.append("Multilingual")
    elif languages_raw:
        languages_cleaned = languages_raw # Assume it's already a list of languages
    else:
        languages_cleaned.append("English") # Default assumption
    api_payload["languages"] = languages_cleaned

    api_payload["architecture"] = data.get("architecture", "Transformer") # Default assumption
    api_payload["parameterCount"] = data.get("parameter_count_approx", 0)
    api_payload["sizeLabel"] = data.get("parameter_size_label", "Unknown")
    api_payload["modelType"] = data.get("modelType", "Language Model")

    # --- Tag Mapping ---
    api_tags = []
    collected_tags = data.get("tags_collected", [])
    tag_mapping_rules = {
        "tools": "Function Calling",
        "24b": "13B-30B Parameters",
        "Text2Text Generation": "Text Generation",
        "mistral": "Mistral Family",
        "apache-2.0": "Apache 2.0",
        "Agentic Coding": "Code Generation",
        "Software Engineering": "Code Generation",
        "3.8b": "3B-7B Parameters",
        # Add more specific mappings as needed based on collected tags
    }

    processed_tags = set()
    for tag_text in collected_tags:
        mapped_tag_name = tag_mapping_rules.get(tag_text, tag_text) # Use mapping or original tag
        if mapped_tag_name in tag_map and mapped_tag_name not in processed_tags:
            api_tags.append({"tagId": tag_map[mapped_tag_name]})
            processed_tags.add(mapped_tag_name)
        else:
            # Try finding a partial match or broader category if direct match fails
            # Example: if tag_text contains 'License', find the specific license tag ID
            pass # Add more sophisticated matching later if needed

    # Add derived tags
    if "Multilingual" in languages_cleaned and "Multilingual" in tag_map and "Multilingual" not in processed_tags:
         api_tags.append({"tagId": tag_map["Multilingual"]})
         processed_tags.add("Multilingual")
    elif "English" in languages_cleaned and "English" in tag_map and "English" not in processed_tags:
         api_tags.append({"tagId": tag_map["English"]})
         processed_tags.add("English")
    # Ensure required fields are not null where API might reject
    # Replace None with empty string or default for potentially problematic fields
    nullable_string_fields = ["template", "modelFile", "digest", "format", "quantizationLevel", "parentModel", "imageUrl"]
    for key in nullable_string_fields:
        if api_payload.get(key) is None:
            api_payload[key] = "" # Use empty string instead of null
            print(f"Warning: Field \t'{key}\t' was null, set to empty string.")

    # Ensure integer fields are not null
    nullable_int_fields = ["quantizationVersion", "fileType", "parameterCount"]
    for key in nullable_int_fields:
        if api_payload.get(key) is None:
            api_payload[key] = 0 # Use 0 instead of null
            print(f"Warning: Field \t'{key}\t' was null, set to 0.")

    # Ensure required fields have some value (even if just 'Unknown')
    required_fields = ["name", "description", "version", "size", "releasedAt", "referenceLink", "license", "parameterSize", "sizeLabel", "modelType"]
    for key in required_fields:
        if api_payload.get(key) is None:
            api_payload[key] = "Unknown" # Or handle appropriately
            print(f"Warning: Field \t'{key}\t' was null, set to \t'Unknown\t'")

    api_payload["tags"] = api_tags   # --- Save Output ---
    output_filename = os.path.join(output_dir, f"{data['name']}_api_payload.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_filename, 'w') as f:
        json.dump(api_payload, f, indent=2)

    print(f"Successfully mapped data for {data['name']} to {output_filename}")
    return output_filename

# --- Example Usage ---
if __name__ == "__main__":
    raw_dir = "data/raw"
    tags_file = "Tags/created_tag_ids.json"
    output_directory = "data/mapped"

    # Find all *_combined.json files in data/raw/
    model_files = glob.glob(os.path.join(raw_dir, "*_combined.json"))

    print(f"Found {len(model_files)} model files to map.")

    for model_file in model_files:
        print(f"Mapping: {model_file}")
        map_model_to_api_schema(model_file, tags_file, output_directory)


