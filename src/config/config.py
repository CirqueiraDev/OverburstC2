import json, os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

def configs():
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        return f'[!] {CONFIG_PATH} not found!'
    