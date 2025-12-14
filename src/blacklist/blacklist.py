import os, json

BLACKLIST_PATH = os.path.join(os.path.dirname(__file__), 'blacklist.json')

def load_blacklist():
    try:
        with open(BLACKLIST_PATH, 'r') as f:
            data = json.load(f)
        return data.get("blacklist", [])
    except FileNotFoundError:
        return []

def save_blacklist(blacklist):
    with open(BLACKLIST_PATH, 'w') as f:
        json.dump({"blacklist": blacklist}, f, indent=2)

def is_blacklisted(ip):
    blacklist = load_blacklist()
    return ip in blacklist

def add_to_blacklist(ip):
    blacklist = load_blacklist()
    if ip in blacklist:
        return f"IP {ip} is already in the blacklist."
    
    blacklist.append(ip)
    save_blacklist(blacklist)
    return f"IP {ip} was successfully added to the blacklist."

def remove_from_blacklist(ip):
    blacklist = load_blacklist()
    if ip not in blacklist:
        return f"IP {ip} is not in the blacklist."
    
    blacklist.remove(ip)
    save_blacklist(blacklist)
    return f"IP {ip} was successfully removed from the blacklist."