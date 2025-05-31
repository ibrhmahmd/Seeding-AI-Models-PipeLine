import json
import os
from datetime import datetime
import glob
import re

def load_json(filepath):
    """Load JSON from a file, return None on error."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON from {filepath}: {e}")
        return None

def enforce_max_length(val, max_len):
    """Truncate string to max_len."""
    if isinstance(val, str) and len(val) > max_len:
        return val[:max_len]
    return val

def is_valid_url(url):
    """Check if a string is a valid http(s) URL."""
    return isinstance(url, str) and re.match(r"^https?://", url)

def sanitize_filename(name):
    """Sanitize a string for use as a filename (Windows-safe)."""
    return re.sub(r'[^\w\-_\. ]', '_', name)

def map_fields(data):
    """Map model data fields to API schema, return dict."""
    api_payload = {}
    primary_variant_name = data.get("variants", [{}])[0].get("name", data.get("name"))
    api_payload["name"] = enforce_max_length(primary_variant_name, 100)
    description = data.get("full_description", data.get("short_description", "No description available."))
    api_payload["description"] = enforce_max_length(description, 1000)
    version = primary_variant_name.split(':')[-1] if ':' in primary_variant_name else 'latest'
    api_payload["version"] = enforce_max_length(version, 50)
    size = data.get("variants", [{}])[0].get("size_gb", "Unknown")
    api_payload["size"] = enforce_max_length(str(size), 50)
    release_date_str = data.get("updated_at_iso", datetime.now().isoformat())
    if not release_date_str.endswith('Z'):
        release_date_str += 'Z'
    api_payload["releasedAt"] = release_date_str
    reference_link = data.get("source_huggingface_page", data.get("source_ollama_page", ""))
    reference_link = enforce_max_length(reference_link, 500)
    if is_valid_url(reference_link):
        api_payload["referenceLink"] = reference_link
    else:
        safe_name = sanitize_filename(primary_variant_name)
        api_payload["referenceLink"] = f"https://huggingface.co/{safe_name}"
    image_url = data.get("image_url", "https://huggingface.co/mistralai/resolve/main/logo.png")
    image_url = enforce_max_length(image_url, 500)
    api_payload["imageUrl"] = image_url if is_valid_url(image_url) else ""
    api_payload["fromOllama"] = bool(data.get("source_ollama_page"))
    api_payload["license"] = enforce_max_length(data.get("license", "Unknown"), 2000)
    api_payload["template"] = enforce_max_length(data.get("template", ""), 2000)
    api_payload["modelFile"] = enforce_max_length(data.get("modelFile", ""), 2000)
    api_payload["digest"] = enforce_max_length(data.get("digest", ""), 200)
    api_payload["format"] = enforce_max_length(data.get("format", ""), 50)
    api_payload["quantizationLevel"] = enforce_max_length(data.get("quantizationLevel", ""), 50)
    api_payload["quantizationVersion"] = int(data.get("quantizationVersion", 0))
    api_payload["fileType"] = int(data.get("fileType", 0))
    api_payload["parameterSize"] = enforce_max_length(data.get("parameter_size_label", "Unknown"), 50)
    api_payload["parentModel"] = enforce_max_length(data.get("parent_model_hf", ""), 100)
    api_payload["family"] = enforce_max_length(data.get("author", data.get("name", "").split(':')[0]).replace(" AI", ""), 100)
    api_payload["sizeLabel"] = enforce_max_length(data.get("parameter_size_label", "Unknown"), 50)
    api_payload["modelType"] = enforce_max_length(data.get("modelType", "Language Model"), 50)
    api_payload["architecture"] = enforce_max_length(data.get("architecture", "Transformer"), 100)
    param_count = data.get("parameter_count_approx", 0)
    api_payload["parameterCount"] = int(param_count) if int(param_count) > 0 else 0
    fam = api_payload["family"]
    api_payload["families"] = [enforce_max_length(fam, 100)] if fam else []
    languages_raw = data.get("languages_hf", [])
    languages_cleaned = []
    if languages_raw and isinstance(languages_raw, list) and "Multiple" in languages_raw[0]:
        languages_cleaned.append("Multilingual")
    elif languages_raw:
        languages_cleaned = [enforce_max_length(l, 50) for l in languages_raw if l and len(l) <= 50]
    else:
        languages_cleaned.append("English")
    api_payload["languages"] = [l for l in languages_cleaned if l]
    return api_payload, languages_cleaned, primary_variant_name

def map_tags(data, tag_map, languages_cleaned):
    """Map tags from model data to API tag IDs."""
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
    }
    processed_tags = set()
    for tag_text in collected_tags:
        mapped_tag_name = tag_mapping_rules.get(tag_text, tag_text)
        if mapped_tag_name in tag_map and mapped_tag_name not in processed_tags:
            if mapped_tag_name and len(mapped_tag_name) <= 100:
                api_tags.append({"tagId": tag_map[mapped_tag_name]})
            processed_tags.add(mapped_tag_name)
    if "Multilingual" in languages_cleaned and "Multilingual" in tag_map and "Multilingual" not in processed_tags:
        api_tags.append({"tagId": tag_map["Multilingual"]})
        processed_tags.add("Multilingual")
    elif "English" in languages_cleaned and "English" in tag_map and "English" not in processed_tags:
        api_tags.append({"tagId": tag_map["English"]})
        processed_tags.add("English")
    return api_tags

def fill_nulls(api_payload):
    """Ensure required and nullable fields are not null."""
    nullable_string_fields = ["template", "modelFile", "digest", "format", "quantizationLevel", "parentModel", "imageUrl"]
    for key in nullable_string_fields:
        if api_payload.get(key) is None:
            api_payload[key] = ""
            print(f"Warning: Field \t'{key}\t' was null, set to empty string.")
    nullable_int_fields = ["quantizationVersion", "fileType", "parameterCount"]
    for key in nullable_int_fields:
        if api_payload.get(key) is None:
            api_payload[key] = 0
            print(f"Warning: Field \t'{key}\t' was null, set to 0.")
    required_fields = ["name", "description", "version", "size", "releasedAt", "referenceLink", "license", "parameterSize", "sizeLabel", "modelType"]
    for key in required_fields:
        if api_payload.get(key) is None or api_payload.get(key) == "":
            api_payload[key] = "Unknown"
            print(f"Warning: Field \t'{key}\t' was null, set to \t'Unknown\t'")
    if "parameterCount" in api_payload and api_payload["parameterCount"] <= 0:
        api_payload["parameterCount"] = 1
    return api_payload

def save_api_payload(api_payload, output_dir, model_name):
    """Save the API payload to a JSON file with a sanitized filename."""
    safe_name = sanitize_filename(model_name)
    output_filename = os.path.join(output_dir, f"{safe_name}_api_payload.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_filename, 'w') as f:
        json.dump(api_payload, f, indent=2)
    print(f"Successfully mapped data for {model_name} to {output_filename}")
    return output_filename

def map_model_to_api_schema(model_data_path, tags_data_path, output_dir):
    """Main mapping function: loads data, maps fields and tags, fills nulls, saves output."""
    data = load_json(model_data_path)
    if data is None:
        return None
    tag_map = load_json(tags_data_path)
    if tag_map is None:
        return None
    api_payload, languages_cleaned, primary_variant_name = map_fields(data)
    api_tags = map_tags(data, tag_map, languages_cleaned)
    api_payload["tags"] = api_tags
    api_payload = fill_nulls(api_payload)
    return save_api_payload(api_payload, output_dir, primary_variant_name)

# --- Example Usage ---
if __name__ == "__main__":
    enriched_dir = "data/enriched"
    tags_file = "Tags/created_tag_ids.json"
    output_directory = "data/mapped"
    model_files = glob.glob(os.path.join(enriched_dir, "*.json"))
    print(f"Found {len(model_files)} model files to map.")
    for model_file in model_files:
        print(f"Mapping: {model_file}")
        map_model_to_api_schema(model_file, tags_file, output_directory)


