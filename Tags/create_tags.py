import requests
import json
import re
import os

# API Configuration
url = "http://ollamanetgateway.runasp.net/admin/TagOperations"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbjEiLCJqdGkiOiJlOWY3ZDdhNy1kMmRlLTRlODktOWI2Mi01Njc4Y2MzMjU3YzEiLCJlbWFpbCI6ImFkbWluQG9sbGFtYW5ldC5jb20iLCJVc2VySWQiOiI5NjUzOTY1ZC03Y2M4LTQxMWUtODNjNC0zYWY1NDBjOTljMTgiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3JvbGUiOiJBZG1pbiIsImV4cCI6MTc1MDg5MDE1NiwiaXNzIjoiU2VjdXJlQXBpIiwiYXVkIjoiU2VjdXJlQXBpVXNlciJ9.ITw8IYMnOI3eQ6AHUBOzhuWkIawPLpqk0c-O8GeiABk"
headers = {
    "accept": "text/plain",
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# File Paths
proposal_file = "Tags/tag_proposal.md"
log_file = "Tags/created_tags_log.txt"
ids_file = 'Tags/created_tag_ids.json'

# Extract Tags from Markdown
def extract_tags(filename):
    tags = set() # Use a set to avoid duplicates
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Match lines starting with '*   **' and capture text between '**'
                match = re.match(r'^\*   \*\*(.+?)\*\*', line)
                if match:
                    tag_name = match.group(1).strip()
                    # Remove potential trailing colon or parenthesized text if captured by mistake
                    tag_name = re.sub(r'\s*[:\(].*$', '', tag_name).strip()
                    # Handle cases like "FP16 / BF16"
                    if " / " in tag_name:
                        # Split, strip whitespace from each part
                        tags.update([t.strip() for t in tag_name.split("/")])
                    else:
                        tags.add(tag_name)
    except FileNotFoundError:
        print(f"Error: File not found - {filename}")
        return []
    # Filter out any empty strings that might have resulted
    tags = {tag for tag in tags if tag}
    return sorted(list(tags))

# Create Tags via API
def create_tag(tag_name):
    payload = json.dumps({"name": tag_name})
    try:
        # Increased timeout for potentially slow API
        response = requests.post(url, headers=headers, data=payload, timeout=60)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        # Attempt to parse the response as JSON to get the ID
        try:
            response_data = response.json()
            # Assuming the ID is directly in the response or under a key like 'id' or 'tagId'
            tag_id = response_data.get('id') or response_data.get('tagId') or response_data
            return {"status": "success", "id": tag_id, "raw_response": response.text}
        except json.JSONDecodeError:
            # If response is not JSON, return the raw text
            return {"status": "success_non_json", "id": None, "raw_response": response.text}
    except requests.exceptions.Timeout:
        return {"status": "error", "message": f"Timeout error creating tag '{tag_name}'"}
    except requests.exceptions.RequestException as e:
        error_message = f"Error creating tag '{tag_name}': {e}"
        if e.response is not None:
            error_message += f" | Response: {e.response.status_code} {e.response.text}"
        return {"status": "error", "message": error_message}

# Main Execution
if __name__ == "__main__":
    extracted_tags = extract_tags(proposal_file)
    results = {}
    created_tag_ids = {}

    if not extracted_tags:
        print("No tags extracted. Please check the regex and file format. Exiting.")
    else:
        print(f"Found {len(extracted_tags)} unique tags to create:")
        print(extracted_tags)
        print("--- Starting Tag Creation ---")
        with open(log_file, 'w') as log:
            log.write("--- Tag Creation Log ---\n")
            for tag in extracted_tags:
                print(f"Creating tag: {tag}...")
                result = create_tag(tag)
                print(f"  Result: {result}")
                log.write(f"Tag: {tag}\nResult: {json.dumps(result)}\n---\n")
                results[tag] = result
                if result["status"].startswith("success") and result.get("id"):
                     created_tag_ids[tag] = result["id"]
                elif result["status"].startswith("success"):
                    # Handle cases where ID might be in raw text if not JSON
                    # This part might need adjustment based on actual API response format
                    print(f"  Warning: Tag '{tag}' created but ID not found in JSON response. Raw: {result['raw_response']}")
                    # Try a simple regex for UUID as a fallback
                    uuid_match = re.search(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', result['raw_response'])
                    if uuid_match:
                        found_id = uuid_match.group(0)
                        print(f"  Attempting to use extracted UUID: {found_id}")
                        created_tag_ids[tag] = found_id
                    else:
                         created_tag_ids[tag] = f"CREATED_CHECK_LOG: {result['raw_response']}" # Mark for manual check
                else:
                    print(f"  Failed to create tag: {tag}")

        print(f"--- Tag creation process finished. Results logged to {log_file} ---")

    # Save the successfully created tag names and their IDs to a separate file
    if created_tag_ids:
        print(f"Saving successfully created tag IDs to {ids_file}")
        with open(ids_file, 'w') as json_log:
            json.dump(created_tag_ids, json_log, indent=2)
    else:
        print("No tags were successfully created or IDs extracted.")

