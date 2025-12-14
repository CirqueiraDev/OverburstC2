import re
import ipaddress

def validate_username(username, max_len=32):
    if not username or len(username) > max_len:
        return False
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False
    return True

def validate_ip(ip):
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

def validate_port(port, rand=False):
    if not port.isdigit():
        return False
        
    port_num = int(port)
    if rand:
        return 0 <= port_num <= 65535
    else:
        return 1 <= port_num <= 65535

def validate_time(time_str, min_time=10, max_time=1300):
    if not time_str.isdigit():
        return False
        
    time_num = int(time_str)
    return min_time <= time_num <= max_time

