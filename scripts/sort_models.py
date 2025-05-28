import json
import re
from datetime import datetime, timedelta

# Read the raw model data
input_file = 'data/raw/ollama_models_raw.json'
output_file = 'data/processed/ollama_models_sorted.json'

def parse_pulls(pulls_text):
    if not pulls_text:
        return 0
    match = re.search(r'([\d,]+)', pulls_text)
    if match:
        return int(match.group(1).replace(',', ''))
    return 0

def parse_updated_time(updated_text):
    if not updated_text:
        # Assign a very old date if no update info
        return datetime.now() - timedelta(days=365*10)

    match = re.search(r'Updated\u00a0 (\d+) (day|week|month|year)s? ago', updated_text)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if unit == 'day':
            delta = timedelta(days=num)
        elif unit == 'week':
            delta = timedelta(weeks=num)
        elif unit == 'month':
            # Approximate month as 30 days
            delta = timedelta(days=num * 30)
        elif unit == 'year':
            delta = timedelta(days=num * 365)
        else:
            delta = timedelta(days=365*10) # Default large delta if unit unknown
        return datetime.now() - delta
    else:
        # Assign a very old date if format is unexpected
        return datetime.now() - timedelta(days=365*10)

try:
    with open(input_file, 'r') as f:
        models = json.load(f)
except FileNotFoundError:
    print(f"Error: Input file {input_file} not found.")
    exit()
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {input_file}.")
    exit()

# Parse and add sortable fields
for model in models:
    model['pulls_count'] = parse_pulls(model.get('pulls_text', ''))
    model['updated_at'] = parse_updated_time(model.get('updated_text', ''))

# Sort models: primarily by updated_at (most recent first), secondarily by pulls_count (highest first)
# Convert datetime to timestamp for sorting if needed, or rely on direct comparison
sorted_models = sorted(models, key=lambda x: (x['updated_at'], x['pulls_count']), reverse=True)

# Remove temporary sort fields before saving
for model in sorted_models:
    del model['pulls_count']
    # Convert datetime back to string or keep as is depending on desired output format
    model['updated_at'] = model['updated_at'].isoformat()

# Limit to top 100 as requested
top_100_models = sorted_models[:100]

# Save the sorted list
with open(output_file, 'w') as f:
    json.dump(top_100_models, f, indent=2)

print(f"Successfully sorted models and saved top 100 to {output_file}")

