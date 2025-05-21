import os, json

BLACKLIST_PATH = os.path.join(os.path.dirname(__file__), 'blacklist.json')

def load_blacklist():
    """Carrega a blacklist do arquivo JSON."""
    try:
        with open(BLACKLIST_PATH, 'r') as f:
            data = json.load(f)
        return data.get("blacklist", [])
    except FileNotFoundError:
        return []

def save_blacklist(blacklist):
    """Salva a blacklist atualizada no arquivo JSON."""
    with open(BLACKLIST_PATH, 'w') as f:
        json.dump({"blacklist": blacklist}, f, indent=2)

def is_blacklisted(ip):
    """Verifica se um IP está na blacklist. True se o IP estiver na blacklist, False caso contrário"""
    blacklist = load_blacklist()
    return ip in blacklist

def add_to_blacklist(ip):
    """Adiciona um IP à blacklist. Mensagem informando o resultado da operação"""
    blacklist = load_blacklist()
    if ip in blacklist:
        return f"IP {ip} is already in the blacklist."
    
    blacklist.append(ip)
    save_blacklist(blacklist)
    return f"IP {ip} was successfully added to the blacklist."

def remove_from_blacklist(ip):
    """Remove um IP da blacklist. Mensagem informando o resultado da operação"""
    blacklist = load_blacklist()
    if ip not in blacklist:
        return f"IP {ip} is not in the blacklist."
    
    blacklist.remove(ip)
    save_blacklist(blacklist)
    return f"IP {ip} was successfully removed from the blacklist."