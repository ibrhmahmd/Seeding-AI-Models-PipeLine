from huggingface_hub import HfApi, ModelCard
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image
import re

def get_model_data(model_id: str) -> dict:
    # Initialize API
    api = HfApi()
    
    # Get model info
    model_info = api.model_info(repo_id=model_id)
    
    # Get model card (for image extraction)
    card = ModelCard.load(model_id)
    
    # Extract first image URL from model card
    image_match = re.search(r'!\[.*?\]\((.*?)\)', card.content)
    image_url = image_match.group(1) if image_match else None
    
    # If no image found, use owner's avatar
    if not image_url:
        owner = model_id.split("/")[0]
        owner_info = api.user_info(owner)
        image_url = owner_info.avatar_url
    
    # Calculate total repository size
    repo_size = sum(f.size for f in model_info.siblings if f.size is not None)
    
    # Format size (bytes to human-readable)
    size_str = f"{repo_size / (1024 ** 3):.1f}GB" if repo_size > 0 else "Unknown"
    
    # Fill JSON template
    return {
        "name": model_id.split("/")[-1],
        "description": model_info.card_data.get("description", "No description"),
        "version": model_info.card_data.get("version", "1.0"),
        "size": size_str,
        "releasedAt": model_info.lastModified.isoformat(),
        "referenceLink": f"https://huggingface.co/{model_id}",
        "imageUrl": image_url,
        "license": model_info.card_data.get("license", "Unknown"),
        "template": "string",  # Placeholder
        "modelFile": "model.safetensors",  # Most common
        "digest": "string",    # Placeholder
        "format": "SafeTensors",
        "parameterSize": f"{model_info.config.get('num_parameters', 0) / 1e9:.1f}B",
        "quantizationLevel": "string",  # Placeholder
        "parentModel": model_info.card_data.get("base_model", "Unknown"),
        "family": model_info.config.get("model_type", "Unknown"),
        "families": [model_info.config.get("model_type", "Unknown")],
        "languages": model_info.card_data.get("language", ["en"]),
        "architecture": model_info.config.get("architectures", ["Unknown"])[0],
        "fileType": 0,  # 0=SafeTensors
        "parameterCount": model_info.config.get("num_parameters", 0),
        "quantizationVersion": 0,  # Placeholder
        "sizeLabel": f"{model_info.config.get('num_parameters', 0) / 1e9:.1f}B"
    }

# Example Usage
model_id = "llama3.2-1b"  # Replace with your model ID
model_data = get_model_data(model_id)
print(model_data)