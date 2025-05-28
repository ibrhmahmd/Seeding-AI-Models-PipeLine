import requests
import json
import os
import time

# Configuration
api_url = "http://ollamanetgateway.runasp.net/admin/AIModelOperations"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbjEiLCJqdGkiOiJlOWY3ZDdhNy1kMmRlLTRlODktOWI2Mi01Njc4Y2MzMjU3YzEiLCJlbWFpbCI6ImFkbWluQG9sbGFtYW5ldC5jb20iLCJVc2VySWQiOiI5NjUzOTY1ZC03Y2M4LTQxMWUtODNjNC0zYWY1NDBjOTljMTgiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3JvbGUiOiJBZG1pbiIsImV4cCI6MTc1MDg5MDE1NiwiaXNzIjoiU2VjdXJlQXBpIiwiYXVkIjoiU2VjdXJlQXBpVXNlciJ9.ITw8IYMnOI3eQ6AHUBOzhuWkIawPLpqk0c-O8GeiABk"
headers = {
    "accept": "text/plain",
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
data_dir = "data/processed"
log_file = "logs/seed_models_log.txt"

# Function to seed a model via API
def seed_model(payload):
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=60) # Increased timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return True, f"Success: Status Code {response.status_code}, Response: {response.text[:500]}..." # Log truncated response
    except requests.exceptions.RequestException as e:
        return False, f"Error: {e}"
    except json.JSONDecodeError as e:
        # This might happen if the response is not valid JSON, but the request might have succeeded (e.g., 201 Created with no body)
        if response.status_code in [200, 201, 204]:
             return True, f"Success: Status Code {response.status_code}, Response: (non-JSON) {response.text[:500]}..."
        else:
            return False, f"Error: Failed to decode JSON response. Status: {response.status_code}, Response: {response.text[:500]}... Error: {e}"

# --- Main Execution ---

# Clear previous log file
if os.path.exists(log_file):
    os.remove(log_file)

successful_seeds = 0
failed_seeds = 0

with open(log_file, 'a') as log:
    log.write(f"Starting model seeding process at {time.ctime()}\n")
    log.write(f"Target API: {api_url}\n")
    log.write(f"Reading data from: {data_dir}\n\n")

    if not os.path.isdir(data_dir):
        message = f"Error: Data directory {data_dir} not found."
        print(message)
        log.write(message + "\n")
    else:
        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(data_dir, filename)
                log.write(f"Processing file: {filename}\n")
                print(f"Processing file: {filename}")
                try:
                    with open(filepath, 'r') as f:
                        model_data = json.load(f)

                    # Attempt to seed the model
                    success, message = seed_model(model_data)
                    log.write(f"  Result: {message}\n")
                    print(f"  Result: {message}")

                    if success:
                        successful_seeds += 1
                    else:
                        failed_seeds += 1

                except json.JSONDecodeError as e:
                    message = f"  Error reading JSON from {filename}: {e}"
                    print(message)
                    log.write(message + "\n")
                    failed_seeds += 1
                except IOError as e:
                    message = f"  Error opening file {filename}: {e}"
                    print(message)
                    log.write(message + "\n")
                    failed_seeds += 1
                except Exception as e:
                    message = f"  An unexpected error occurred processing {filename}: {e}"
                    print(message)
                    log.write(message + "\n")
                    failed_seeds += 1

                time.sleep(1)

    summary = f"\nFinished model seeding process at {time.ctime()}\n"
    summary += f"Successfully seeded: {successful_seeds}\n"
    summary += f"Failed seeds: {failed_seeds}\n"
    print(summary)
    log.write(summary)

print(f"Seeding process complete. Check {log_file} for details.")

