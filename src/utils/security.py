import re
import hmac
import hashlib
import secrets
import time
from collections import defaultdict

def sanitize_log(text):
    return re.sub(r'[\r\n\t]', '', str(text))[:200]

def sanitize_command(cmd):
    if not cmd:
        return ''
    cmd = re.sub(r'[^\w\s.-]', '', str(cmd))
    return cmd[:100]

def generate_session_token():
    return secrets.token_urlsafe(32)

def verify_bot_auth(password, arch, bot_secret):
    expected = hmac.new(bot_secret, arch.encode('utf-8'), hashlib.sha256).hexdigest()
    return hmac.compare_digest(password, expected)

class RateLimiter:
    def __init__(self, max_attempts=5, window_seconds=300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.login_attempts = defaultdict(list)
        self.lock = None
    
    def set_lock(self, lock):
        self.lock = lock
    
    def check_rate_limit(self, address):
        ip = address[0]
        now = time.time()
        
        if self.lock:
            with self.lock:
                return self._check(ip, now)
        else:
            return self._check(ip, now)
    
    def _check(self, ip, now):
        self.login_attempts[ip] = [t for t in self.login_attempts[ip] if now - t < self.window_seconds]
        if len(self.login_attempts[ip]) >= self.max_attempts:
            return False
        self.login_attempts[ip].append(now)
        return True
    
    def cleanup(self):
        now = time.time()
        if self.lock:
            with self.lock:
                for ip in list(self.login_attempts.keys()):
                    self.login_attempts[ip] = [t for t in self.login_attempts[ip] if now - t < self.window_seconds]
                    if not self.login_attempts[ip]:
                        del self.login_attempts[ip]

