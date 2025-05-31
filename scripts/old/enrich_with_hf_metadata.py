import os
import json
import requests
import re
from urllib.parse import quote
from typing import Optional, Dict, Any

PROCESSED_DIR = 'data/processed'
ENRICHED_DIR = 'data/enriched'
LOG_FILE = 'logs/enrich_with_hf_metadata.log'
HF_API_MODEL_URL = 'https://huggingface.co/api/models/'
HF_MODEL_PAGE = 'https://huggingface.co/'

os.makedirs(ENRICHED_DIR, exist_ok=True)

def log(msg: str) -> None:
    """Append a message to the log file and print it."""
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')
    print(msg)

def load_model_json(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a model JSON file and return its data as a dict."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        log(f"ERROR: Failed to load {filepath}: {e}")
        return None

def save_model_json(filepath: str, data: Dict[str, Any]) -> None:
    """Save the model data as JSON to the given filepath."""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log(f"ERROR: Failed to save {filepath}: {e}")

def get_hf_metadata(model_name: str) -> Optional[Dict[str, Any]]:
    """
    Query Hugging Face API for model metadata.
    Returns dict with description, referenceLink, imageUrl, size_bytes, or dummy data if not found.
    """
    url = HF_API_MODEL_URL + quote(model_name)
    resp = requests.get(url)
    if resp.status_code != 200:
        log(f"WARNING: Model '{model_name}' not found on Hugging Face (status {resp.status_code}), using dummy data.")
        # Return dummy data for pipeline testing
        return {
            'description': f'Dummy description for {model_name}.',
            'referenceLink': f'https://huggingface.co/dummy/{quote(model_name)}',
            'imageUrl': 'https://huggingface.co/front/assets/huggingface_logo-noborder.svg',
            'size': 123456789
        }
    data = resp.json()
    # Description
    description = data.get('cardData', {}).get('summary') or data.get('cardData', {}).get('description') or data.get('pipeline_tag', '')
    if description:
        description = description.strip().replace('\n', ' ')
        if len(description) > 1000:
            description = description[:997] + '...'
    else:
        description = 'No description available.'
    # Reference link
    reference_link = HF_MODEL_PAGE + data['modelId']
    # Image URL: try model card images, then repo social preview
    image_url = extract_image_url(data)
    # Size: sum all .bin or .safetensors files
    size_bytes = sum(
        file.get('size', 0)
        for file in data.get('siblings', [])
        if re.search(r'\.(bin|safetensors)$', file['rfilename'], re.IGNORECASE)
    )
    return {
        'description': description,
        'referenceLink': reference_link,
        'imageUrl': image_url,
        'size': size_bytes
    }

def extract_image_url(data: Dict[str, Any]) -> str:
    """Extract the first image URL from Hugging Face model data."""
    # Try model card image
    if 'cardData' in data and 'image' in data['cardData']:
        image_url = data['cardData']['image']
        if not image_url.startswith('http'):
            image_url = HF_MODEL_PAGE + data['modelId'] + '/resolve/main/' + image_url.lstrip('/')
        return image_url
    # Try repo's first file that looks like an image
    for file in data.get('siblings', []):
        if re.search(r'\.(png|jpg|jpeg|gif)$', file['rfilename'], re.IGNORECASE):
            return HF_MODEL_PAGE + data['modelId'] + '/resolve/main/' + file['rfilename']
    # Fallback: empty string
    return ''

def enrich_model_with_hf(model_data: Dict[str, Any], hf_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Update the model data dict with Hugging Face metadata."""
    model_data['description'] = hf_meta['description']
    model_data['referenceLink'] = hf_meta['referenceLink']
    model_data['imageUrl'] = hf_meta['imageUrl']
    model_data['size'] = hf_meta['size']
    return model_data

def process_all_models():
    """Main workflow: enrich all processed models with Hugging Face metadata."""
    # Clear log file
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    for fname in os.listdir(PROCESSED_DIR):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(PROCESSED_DIR, fname)
        model_data = load_model_json(fpath)
        if not model_data:
            continue
        model_name = model_data.get('name')
        if not model_name:
            log(f"WARNING: No 'name' field in {fname}, skipping.")
            continue
        hf_meta = get_hf_metadata(model_name)
        if not hf_meta:
            log(f"WARNING: Could not fetch Hugging Face metadata for {model_name}.")
            continue
        enriched = enrich_model_with_hf(model_data, hf_meta)
        outpath = os.path.join(ENRICHED_DIR, fname)
        save_model_json(outpath, enriched)
        log(f"Enriched {fname} with Hugging Face metadata.")

if __name__ == '__main__':
    process_all_models() 