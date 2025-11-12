import json
import os


def load_api_key() -> str:
    """
    Loads the YouTube API key from config/api_key.json.
    If the file or folder doesn't exist, it creates them with a placeholder key.
    Returns the API key string (or an empty string if not set).
    """
    # Define the path: ../config/api_key.json
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'api_key.json')

    # Ensure the config directory exists
    config_dir = os.path.dirname(config_path)
    if config_dir and not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)

    api_key = ''

    # If config file doesn't exist, create it with a placeholder key
    if not os.path.exists(config_path):
        default_data = {"api_key": "YOUR_YOUTUBE_API_KEY_HERE"}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4)
        print(f"[INFO] Created new config file at: {config_path}")
        print("[INFO] Please open this file and replace the placeholder with your actual API key.")
    else:
        # Try to read API key from the existing file
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            api_key = data.get('api_key') or data.get('API_KEY') or data.get('YOUTUBE_API_KEY') or ''
        except Exception as e:
            print(f"[WARNING] Could not read the API key file ({e}).")
            api_key = ''

    if not api_key or api_key == "YOUR_YOUTUBE_API_KEY_HERE":
        print(f"[WARNING] No valid API key found in {config_path}. Please update it.")

    return api_key