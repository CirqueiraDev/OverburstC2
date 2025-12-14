#!/usr/bin/env python3
import json
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(base_dir, 'src', 'config', 'config.json')
config_h_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot', 'config.h')

try:
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    bot_secret = config.get('bot_secret', '')
    
    if not bot_secret:
        print("Error: bot_secret not found in config.json")
        sys.exit(1)
    
    with open(config_h_path, 'r') as f:
        config_h_content = f.read()
    
    new_line = f'#define BOT_SECRET_B64 "{bot_secret}"\n'
    
    if 'BOT_SECRET_B64' in config_h_content:
        lines = config_h_content.split('\n')
        new_lines = []
        for line in lines:
            if line.strip().startswith('#define BOT_SECRET_B64'):
                new_lines.append(new_line.rstrip())
            else:
                new_lines.append(line)
        config_h_content = '\n'.join(new_lines)
    else:
        config_h_content = config_h_content.rstrip() + '\n' + new_line
    
    with open(config_h_path, 'w') as f:
        f.write(config_h_content)
    
    print(f"Updated {config_h_path} with bot_secret from config.json")
    
except FileNotFoundError as e:
    print(f"Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

