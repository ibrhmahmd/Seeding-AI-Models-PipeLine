import json
import os
import re
from datetime import datetime

# Ensure the output directory exists
output_dir = "data/processed"
os.makedirs(output_dir, exist_ok=True)

# Load tag IDs
tags_file = "Tags/created_tag_ids.json"
try:
    with open(tags_file, 'r') as f:
        tag_map = json.load(f)
except FileNotFoundError:
    print(f"Error: Tags file not found at {tags_file}")
    tag_map = {}
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {tags_file}")
    tag_map = {}

def get_tag_id(tag_name):
    tag_id = tag_map.get(tag_name)
    if not tag_id:
        print(f"Warning: Tag ID not found for tag: {tag_name}")
    return tag_id

def format_tags(tags_list):
    return [{"tagId": get_tag_id(tag)} for tag in tags_list if get_tag_id(tag)]

def parse_param_count(param_size_str):
    if not param_size_str:
        return 0
    num_str = re.findall(r"\d+\.?\d*", param_size_str)[0]
    num = float(num_str)
    if 'B' in param_size_str.upper():
        return int(num * 1_000_000_000)
    elif 'M' in param_size_str.upper():
        return int(num * 1_000_000)
    else:
        return int(num) # Assume raw count if no unit

# --- Model Data Definitions ---

models_data = [
    {
        "ollama_name": "llama3:8b-instruct",
        "name": "llama3:8b-instruct", # Using ollama name for consistency for now
        "description": "Instruction tuned version of Meta Llama 3 8B model, optimized for dialogue use cases.",
        "version": "3", # Implicit version
        "size": "4.7GB", # From Ollama page (approx)
        "releasedAt": "2024-04-18T00:00:00.000Z", # From HF
        "referenceLink": "https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct",
        "imageUrl": "https://huggingface.co/meta-llama/resolve/main/Llama_3_logo_color.png", # Found via search
        "license": "Llama 3 License", # Specific license name
        "template": "{{ if .System }}<|start_header_id|>system<|end_header_id|>\n\n{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>\n\n{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>\n\n{{ .Response }}<|eot_id|>", # From Ollama page (simplified)
        "modelFile": "", # Ollama digest for instruct might differ, placeholder
        "digest": "", # Ollama digest for instruct might differ, placeholder
        "format": "GGUF",
        "parameterSize": "8B",
        "quantizationLevel": "Q4_0", # Common default, may vary
        "parentModel": "",
        "family": "Llama",
        "languages": ["English"],
        "architecture": "llama",
        "fileType": 0, # Placeholder
        "quantizationVersion": 4, # Placeholder
        "modelType": "instruct",
        "tags_list": ["Llama Family", "8B Parameters", "Text Generation", "English", "Llama 3 License", "GGUF", "Q4_0", "Instruct"]
    },
    {
        "ollama_name": "mistral:7b",
        "name": "mistral:7b",
        "description": "The 7.3B parameter model released by Mistral AI (v0.3). Outperforms Llama 2 13B on many benchmarks. Supports function calling.",
        "version": "0.3", # Latest version from Ollama page
        "size": "4.1GB", # From Ollama page
        "releasedAt": "2024-05-22T00:00:00.000Z", # v0.3 release date from Ollama page
        "referenceLink": "https://huggingface.co/mistralai/Mistral-7B-v0.3", # Found via search
        "imageUrl": "https://huggingface.co/mistralai/resolve/main/logo.png", # Mistral AI logo
        "license": "Apache License Version 2.0", # From Ollama page
        "template": "{{- if .Messages }}{{- range $index, $_ := .Messages }}{{- if eq .Role \"user\" }}{{- if and (eq (len (slice $.Messages $index)) 1) $.Tools }}\[AVAILABLE_TOOLS\] {{ $.Tools }}\[/AVAILABLE_TOOLS\]\n{{- end }}\[INST\] {{ if and $.System (eq (len (slice $.Messages $index)) 1) }}{{ $.System }}\n{{ end }}{{ .Content }}\[/INST\]\n{{- else if eq .Role \"assistant\" }}{{- if .Content }} {{ .Content }}{{- else if .ToolCalls }}\[TOOL_CALLS\] \[\n{{- range .ToolCalls }}{\"name\": \"{{ .Function.Name }}\", \"arguments\": {{ .Function.Arguments }}}\n{{- end }}\]{{- end }}</s>{{- else if eq .Role \"tool\" }}\[TOOL_RESULTS\] {\"content\": {{ .Content }}} \[/TOOL_RESULTS\]{{- end }}{{- end }}{{- else }}\[INST\] {{ if .System }}{{ .System }}\n{{ end }}{{ .Prompt }}\[/INST\]{{- end }} {{ .Response }}{{- if .Response }}</s>{{- end }}", # From Ollama page
        "modelFile": "ff82381e2bea", # Digest from Ollama page
        "digest": "ff82381e2bea", # Digest from Ollama page
        "format": "GGUF",
        "parameterSize": "7B", # Actually 7.25B on Ollama page
        "quantizationLevel": "Q4_0", # From Ollama page
        "parentModel": "",
        "family": "Mistral",
        "languages": ["English"], # Primarily English
        "architecture": "llama", # Ollama metadata shows llama architecture
        "fileType": 0, # Placeholder
        "quantizationVersion": 4, # Placeholder
        "modelType": "instruct", # Default is instruct
        "tags_list": ["Mistral Family", "7B Parameters", "Text Generation", "English", "Apache 2.0", "GGUF", "Q4_0", "Instruct", "Function Calling"]
    },
    {
        "ollama_name": "qwen2:7b",
        "name": "qwen2:7b",
        "description": "Qwen2 is a new series of large language models from Alibaba group, trained on data in 29 languages. 7B parameter version with 128k token context length.",
        "version": "2", # Implicit version
        "size": "4.4GB", # From Ollama page
        "releasedAt": "2024-06-06T00:00:00.000Z", # Approx release date from HF
        "referenceLink": "https://huggingface.co/Qwen/Qwen2-7B",
        "imageUrl": "https://huggingface.co/Qwen/resolve/main/qwen_logo.png", # Qwen logo
        "license": "Apache License Version 2.0", # From Ollama page
        "template": "{{ if .System }}<|im_start|>system\n{{ .System }}<|im_end|>\n{{ end }}{{ if .Prompt }}<|im_start|>user\n{{ .Prompt }}<|im_end|>\n{{ end }}<|im_start|>assistant\n{{ .Response }}<|im_end|>", # From Ollama page (simplified)
        "modelFile": "43f7a214e532", # Digest from Ollama page
        "digest": "43f7a214e532", # Digest from Ollama page
        "format": "GGUF",
        "parameterSize": "7B", # Actually 7.62B on Ollama page
        "quantizationLevel": "Q4_0", # From Ollama page
        "parentModel": "",
        "family": "Qwen",
        "languages": ["Multilingual"], # Supports 29 languages
        "architecture": "qwen2", # From Ollama metadata
        "fileType": 0, # Placeholder
        "quantizationVersion": 4, # Placeholder
        "modelType": "instruct", # Default is instruct
        "tags_list": ["Qwen Family", "7B Parameters", "Text Generation", "Multilingual", "Apache 2.0", "GGUF", "Q4_0", "Instruct"]
    },
    {
        "ollama_name": "llava:7b",
        "name": "llava:7b",
        "description": "LLaVA (Large Language and Vision Assistant) v1.6. A multimodal model combining a vision encoder and Vicuna 7B for visual and language understanding.",
        "version": "1.6", # From Ollama page
        "size": "4.7GB", # From Ollama page
        "releasedAt": "2024-01-30T00:00:00.000Z", # v1.6 release date from blog
        "referenceLink": "https://huggingface.co/liuhaotian/llava-v1.6-vicuna-7b",
        "imageUrl": "https://ollama.com/public/llava.png", # From Ollama site
        "license": "Apache License Version 2.0", # From Ollama page
        "template": "{{ if .System }}System: {{ .System }}\n{{ end }}User: {{ if .Images }}{{ range .Images }}<image> {{ end }}{{ end }}{{ .Prompt }}\nAssistant: {{ .Response }}", # From Ollama page (simplified)
        "modelFile": "8dd30f6b0cb1", # Digest from Ollama page
        "digest": "8dd30f6b0cb1", # Digest from Ollama page
        "format": "GGUF",
        "parameterSize": "7B", # Vicuna 7B base
        "quantizationLevel": "Q4_0", # From Ollama page
        "parentModel": "Vicuna-7B", # Based on Vicuna
        "family": "LLaVA",
        "languages": ["English"],
        "architecture": "llama", # From Ollama metadata
        "fileType": 0, # Placeholder
        "quantizationVersion": 4, # Placeholder
        "modelType": "vision",
        "tags_list": ["LLaVA Family", "7B Parameters", "Multimodal", "Vision", "English", "Apache 2.0", "GGUF", "Q4_0"]
    },
    {
        "ollama_name": "codellama:7b",
        "name": "codellama:7b",
        "description": "Code Llama 7B model, built on Llama 2, specialized for code generation, completion, and discussion across various programming languages.",
        "version": "1", # Base version
        "size": "3.8GB", # From Ollama page
        "releasedAt": "2023-08-24T00:00:00.000Z", # From Meta blog post
        "referenceLink": "https://huggingface.co/codellama/CodeLlama-7b-hf",
        "imageUrl": "https://huggingface.co/codellama/resolve/main/codellama_logo.png", # Found via search
        "license": "Llama 2 Community License", # From Ollama page
        "template": "[INST] {{ if .System }}{{ .System }} {{ end }}{{ .Prompt }} [/INST]", # From Ollama page
        "modelFile": "8fdf8752f6e6", # Digest from Ollama page
        "digest": "8fdf8752f6e6", # Digest from Ollama page
        "format": "GGUF",
        "parameterSize": "7B", # Actually 6.74B on Ollama page
        "quantizationLevel": "Q4_0", # From Ollama page
        "parentModel": "Llama 2", # Built on Llama 2
        "family": "CodeLlama",
        "languages": ["Multilingual", "Code"], # Supports multiple programming languages
        "architecture": "llama", # From Ollama metadata
        "fileType": 0, # Placeholder
        "quantizationVersion": 4, # Placeholder
        "modelType": "code", # Specialized for code
        "tags_list": ["CodeLlama Family", "7B Parameters", "Code Generation", "Code", "Multilingual", "Llama 2 License", "GGUF", "Q4_0"]
    }
]

# --- Process and Save Models ---

for model in models_data:
    api_payload = {
        "name": model["name"],
        "description": model["description"],
        "version": model["version"],
        "size": model["size"],
        "releasedAt": model.get("releasedAt", datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')),
        "referenceLink": model["referenceLink"],
        "imageUrl": model.get("imageUrl", ""),
        "fromOllama": False,
        "license": model["license"],
        "template": model["template"],
        "modelFile": model["modelFile"],
        "digest": model["digest"],
        "format": model["format"],
        "parameterSize": model["parameterSize"],
        "quantizationLevel": model["quantizationLevel"],
        "parentModel": model.get("parentModel", ""),
        "family": model["family"],
        "families": [model["family"]],
        "languages": model["languages"],
        "architecture": model["architecture"],
        "fileType": model["fileType"],
        "parameterCount": parse_param_count(model["parameterSize"]),
        "quantizationVersion": model["quantizationVersion"],
        "sizeLabel": model["parameterSize"],
        "modelType": model["modelType"],
        "tags": format_tags(model["tags_list"])
    }

    output_filename = os.path.join(output_dir, f"{model['ollama_name'].replace(':', '_')}.json")
    try:
        with open(output_filename, 'w') as f:
            json.dump(api_payload, f, indent=2)
        print(f"Successfully wrote data for {model['name']} to {output_filename}")
    except IOError as e:
        print(f"Error writing file {output_filename}: {e}")

print("Finished preparing pilot batch model data.")


