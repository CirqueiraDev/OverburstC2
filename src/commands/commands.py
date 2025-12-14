import threading, re
from colorama import Fore
from src.database.database import load_users, save_users, add_user, remove_user, get_user
from src.blacklist.blacklist import load_blacklist, add_to_blacklist, remove_from_blacklist, is_blacklisted

def handle_admin_commands(command, args, client, send, username):
    user_data = get_user(username)
    if not user_data or user_data.get("role") != "admin":
        send(client, f"{Fore.RED}You don't have permission to use admin commands!\n")
        return

    if command == "!USER":
        handle_user_command(args, client, send)
    elif command == "!BLACKLIST":
        handle_blacklist_command(args, client, send)
    else:
        send(client, f"{Fore.RED}Unknown admin command: {command}\n")

def handle_user_command(args, client, send):
    gray = Fore.LIGHTBLACK_EX
    C = Fore.LIGHTWHITE_EX
    R = Fore.RED
    G = Fore.GREEN
    
    if len(args) < 2:
        send(client, f"{Fore.YELLOW}Usage: !USER LIST | !USER ADD <username> <password> <plan> | !USER REMOVE <username>\n")
        return

    action = args[1].upper()
    
    if action == "LIST":
        users = load_users()
        if not users:
            send(client, f"{R}No users found in database!\n")
            return
            
        send(client, f"\n{C}Users in database: {G}{len(users)}")
        send(client, f"\n{gray}Username{' '*10}Role{' '*8}Plan{' '*8}Expires")
        send(client, f"{gray}-----------------------------------------------------")
        
        for user in users:
            username = user.get("username", "unknown")
            role = user.get("role", "user")
            plan = user.get("plan", "basic")
            expires = user.get("expires_at", "never")
            
            send(client, f"{C}{username:<18}{role:<12}{plan:<12}{expires}")
        send(client, "")
        
    elif action == "ADD":
        if len(args) < 7:
            send(client, f"{Fore.YELLOW}Usage: !USER ADD <username> <password> <plan> <role> <expires in days>\n")
            return
        
        username = args[2].strip()
        password = args[3].strip()
        plan = args[4].strip().lower()
        role = args[5].strip().lower()
        expires_str = args[6].strip()
        
        if not username or len(username) > 32:
            send(client, f"{R}Invalid username! Must be 1-32 characters.\n")
            return
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            send(client, f"{R}Invalid username format! Only alphanumeric, underscore, and dash allowed.\n")
            return
        
        if not password or len(password) < 4 or len(password) > 128:
            send(client, f"{R}Invalid password! Must be 4-128 characters.\n")
            return
        
        if not expires_str.isdigit():
            send(client, f"{R}Invalid expiry days! Must be a number.\n")
            return
        
        try:
            expires = int(expires_str)
            if expires < 1 or expires > 3650:
                send(client, f"{R}Invalid expiry days! Must be between 1 and 3650.\n")
                return
        except (ValueError, OverflowError):
            send(client, f"{R}Invalid expiry days! Must be a valid number.\n")
            return
        
        if get_user(username):
            send(client, f"{R}User {username} already exists!\n")
            return

        valid_plans = ["basic", "premium", "vip"]
        if plan not in valid_plans:
            send(client, f"{R}Invalid plan! Choose from: {', '.join(valid_plans)}\n")
            return
        
        valid_role = ["user", "admin"]
        if role not in valid_role:
            send(client, f"{R}Invalid role! Choose from: {', '.join(valid_role)}\n")
            return

        if add_user(username, password, plan, role, expires):
            send(client, f"{G}User {username} with plan {plan} added successfully!\n")
            return
        
        send(client, f"{R}User {username} with plan {plan} NOT ADDED!\n")
        
    elif action == "REMOVE":
        if len(args) < 3:
            send(client, f"{Fore.YELLOW}Usage: !USER REMOVE <username>\n")
            return
            
        username = args[2].strip()
        
        if not username or len(username) > 32:
            send(client, f"{R}Invalid username!\n")
            return
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            send(client, f"{R}Invalid username format!\n")
            return
        
        user = get_user(username)
        
        if not user:
            send(client, f"{R}User {username} not found!\n")
            return
            
        users = load_users()
        users = [u for u in users if u['username'] != username]
        save_users(users)
        send(client, f"{G}User {username} removed successfully!\n")
        
    else:
        send(client, f"{R}Unknown user command: {action}\n")
        
def handle_blacklist_command(args, client, send):
    gray = Fore.LIGHTBLACK_EX
    C = Fore.LIGHTWHITE_EX
    R = Fore.RED
    G = Fore.GREEN
    
    if len(args) < 2:
        send(client, f"{Fore.YELLOW}Usage: !BLACKLIST LIST | !BLACKLIST ADD <ip> | !BLACKLIST REMOVE <ip>\n")
        return

    action = args[1].upper()
    
    if action == "LIST":
        blacklist = load_blacklist()
        if not blacklist:
            send(client, f"{R}Blacklist is empty!\n")
            return
            
        send(client, f"\n{C}Blacklisted IPs: {G}{len(blacklist)}")
        send(client, f"\n{gray}IP Address")
        send(client, f"{gray}---------------")
        
        for ip in blacklist:
            send(client, f"{C}{ip}")
        send(client, "")
        
    elif action == "ADD":
        if len(args) < 3:
            send(client, f"{Fore.YELLOW}Usage: !BLACKLIST ADD <ip>\n")
            return
            
        ip = args[2]

        import re
        pattern = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')
        if not pattern.match(ip):
            send(client, f"{R}Invalid IP format!\n")
            return
            
        result = add_to_blacklist(ip)
        if "successfully" in result:
            send(client, f"{G}{result}\n")
        else:
            send(client, f"{R}{result}\n")
        
    elif action == "REMOVE":
        if len(args) < 3:
            send(client, f"{Fore.YELLOW}Usage: !BLACKLIST REMOVE <ip>\n")
            return
            
        ip = args[2]
        result = remove_from_blacklist(ip)
        
        if "successfully" in result:
            send(client, f"{G}{result}\n")
        else:
            send(client, f"{R}{result}\n")
        
    else:
        send(client, f"{R}Unknown blacklist command: {action}\n")


# Verificar comandos de administração
# if command.startswith('!'):
#     from src.commands.commands import handle_admin_commands
#     handle_admin_commands(command, args, client, send, username)
#     send(client, prompt, False)
#     continue
