import logging
import time
import threading
from src.utils.validators import validate_ip, validate_port, validate_time
from src.utils.security import sanitize_log, sanitize_command
from src.blacklist.blacklist import is_blacklisted
from colorama import Fore

class AttackManager:
    def __init__(self, attacks_dict, global_limits, locks, bot_manager, send_func, broadcast_func):
        self.attacks = attacks_dict
        self.global_limits = global_limits
        self.locks = locks
        self.bot_manager = bot_manager
        self.send = send_func
        self.broadcast = broadcast_func
    
    def can_launch(self, ip, port, secs, username, client):
        max_attacks = self.global_limits.get("max_attacks", 100)

        if is_blacklisted(ip):
            self.send(client, f'{Fore.RED}Target is blacklisted!\n')
            return False
            
        if not validate_ip(ip):
            self.send(client, f'{Fore.RED}Invalid IP address\n')
            return False
            
        if not validate_port(port):
            self.send(client, f'{Fore.RED}Invalid port number (1-65535)\n')
            return False
        
        min_time = self.global_limits.get("min_time", 10)
        max_time = self.global_limits.get("max_time", 1300)
        if not validate_time(secs, min_time, max_time):
            self.send(client, f'{Fore.RED}Invalid attack duration ({min_time}-{max_time} seconds)\n')
            return False
        
        with self.locks['attacks']:
            if len(self.attacks) >= max_attacks:
                self.send(client, f'{Fore.RED}No slots available!\n')
                return False
                
            if username in self.attacks:
                self.send(client, f'{Fore.RED}Attack already sent!\n')
                return False
                
            for user, info in self.attacks.items():
                if info['target'] == ip:
                    self.send(client, f'{Fore.RED}Target is already under flood, don\'t abuse it!\n')
                    return False
                
        return True
    
    def launch(self, username, ip, port, secs, method):
        with self.locks['attacks']:
            self.attacks[username] = {'target': ip, 'duration': secs, 'method': method}
        
        threading.Thread(target=self._remove_after_timeout, args=(username, int(secs)), daemon=True).start()
        logging.info(f"Ataque iniciado: {sanitize_log(username)} => {ip}:{port} ({method}) por {secs}s")
    
    def stop(self, username):
        with self.locks['attacks']:
            if username in self.attacks:
                del self.attacks[username]
                return True
        return False
    
    def _remove_after_timeout(self, username, timeout):
        time.sleep(timeout)
        with self.locks['attacks']:
            if username in self.attacks:
                logging.info(f"Ataque de {sanitize_log(username)} finalizado (timeout)")
                del self.attacks[username]
    
    def get_count(self):
        with self.locks['attacks']:
            return len(self.attacks)

