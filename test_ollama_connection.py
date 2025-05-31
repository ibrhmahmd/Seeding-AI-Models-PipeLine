import requests

print('Testing connection to Ollama API...')
try:
    response = requests.get('http://localhost:11434/api/tags', timeout=5)
    if response.status_code == 200:
        print('Successfully connected to Ollama API')
        print('Response:', response.json())
    else:
        print(f'Failed to connect to Ollama API. Status code: {response.status_code}')
        print('Response text:', response.text)
except requests.exceptions.RequestException as e:
    print(f'Error connecting to Ollama API: {str(e)}')
except Exception as e:
    print(f'Unexpected error: {str(e)}')
finally:
    print('Test completed.')
