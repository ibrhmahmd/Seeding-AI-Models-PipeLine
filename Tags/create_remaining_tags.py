import requests
import json
import re
import time
import os

# Configuration
api_url = "http://ollamanetgateway.runasp.net/admin/TagOperations"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbjEiLCJqdGkiOiJlOWY3ZDdhNy1kMmRlLTRlODktOWI2Mi01Njc4Y2MzMjU3YzEiLCJlbWFpbCI6ImFkbWluQG9sbGFtYW5ldC5jb20iLCJVc2VySWQiOiI5NjUzOTY1ZC03Y2M4LTQxMWUtODNjNC0zYWY1NDBjOTljMTgiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3JvbGUiOiJBZG1pbiIsImV4cCI6MTc1MDg5MDE1NiwiaXNzIjoiU2VjdXJlQXBpIiwiYXVkIjoiU2VjdXJlQXBpVXNlciJ9.ITw8IYMnOI3eQ6AHUBOzhuWkIawPLpqk0c-O8GeiABk"
headers = {
    "accept": "text/plain",
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
input_tags_file = "Tags/remaining_missing_tags.md"
ids_file = "Tags/created_tag_ids.json"
log_file = "Tags/created_tags_log.txt"

# Function to extract tag names from the markdown file
def extract_tags(filename):
    tags = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Match lines starting with '- ' and capture the rest
                match = re.match(r'^- (.+)', line)
                if match:
                    tag_name = match.group(1).strip()
                    tags.append(tag_name)
    except FileNotFoundError:
        print(f"Error: Input tags file not found at {filename}")
    return tags

# Function to create a tag via API
def create_tag(tag_name):
    payload = json.dumps({"name": tag_name})
    try:
        response = requests.post(api_url, headers=headers, data=payload, timeout=30)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        # Assuming the response body contains the Tag ID directly or within a JSON structure
        # Adjust parsing based on actual API response format
        try:
            # Try parsing as JSON first
            response_data = response.json()
            # Look for common ID fields, adjust as needed
            tag_id = response_data.get('id') or response_data.get('tagId') or response_data.get('TagId')
            if tag_id:
                 return tag_id, f"Success: Created tag '{tag_name}' with ID {tag_id}. Status: {response.status_code}"
            else:
                 # If no ID found in JSON, maybe it's plain text?
                 # Or maybe the ID is the whole response text?
                 tag_id_text = response.text.strip()
                 # Basic check if it looks like a UUID or similar ID format
                 if re.match(r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$', tag_id_text):
                     return tag_id_text, f"Success: Created tag '{tag_name}' with ID {tag_id_text} (plain text response). Status: {response.status_code}"
                 else:
                     return None, f"Warning: Created tag '{tag_name}' but could not extract ID from response: {response.text}. Status: {response.status_code}"

        except json.JSONDecodeError:
             # If JSON parsing fails, treat response as plain text ID
             tag_id_text = response.text.strip()
             # Basic check if it looks like a UUID or similar ID format
             if re.match(r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$', tag_id_text):
                 return tag_id_text, f"Success: Created tag '{tag_name}' with ID {tag_id_text} (plain text response). Status: {response.status_code}"
             else:
                 return None, f"Warning: Created tag '{tag_name}' but response was not JSON and did not look like an ID: {response.text}. Status: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return None, f"Error creating tag '{tag_name}': {e}"

# --- Main Execution ---

# Append to existing log file

# Load existing tag IDs
existing_tag_ids = {}
if os.path.exists(ids_file):
    try:
        with open(ids_file, 'r') as f:
            existing_tag_ids = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not load existing tag IDs from {ids_file}. Starting fresh. Error: {e}")
        existing_tag_ids = {} # Start fresh if file is corrupted or not found

tag_names_to_create = extract_tags(input_tags_file)
created_tags = existing_tag_ids # Start with existing tags

with open(log_file, 'a') as log:
    log.write(f"\nStarting creation of remaining tags at {time.ctime()}\n")
    log.write(f"Reading tags from: {input_tags_file}\n")
    log.write(f"Found {len(tag_names_to_create)} tags to create.\n\n")

    for tag_name in tag_names_to_create:
        if tag_name in created_tags:
            message = f"Skipped: Tag '{tag_name}' already exists with ID {created_tags[tag_name]}."
            print(message)
            log.write(message + "\n")
            continue

        tag_id, message = create_tag(tag_name)
        print(message)
        log.write(message + "\n")
        if tag_id:
            created_tags[tag_name] = tag_id
        time.sleep(0.5) # Add a small delay between requests

    log.write(f"\nFinished creation of remaining tags at {time.ctime()}\n")

# Save the updated dictionary of tag IDs
try:
    with open(ids_file, 'w') as f:
        json.dump(created_tags, f, indent=2)
    print(f"Successfully updated tag IDs in {ids_file}")
except IOError as e:
    print(f"Error writing updated tag IDs to {ids_file}: {e}")

