import time
import secrets

class SessionManager:
    def __init__(self, sessions_dict, locks):
        self.sessions = sessions_dict
        self.locks = locks
    
    def create(self, username, address):
        token = secrets.token_urlsafe(32)
        with self.locks['sessions']:
            self.sessions[token] = {
                'username': username,
                'address': address,
                'created_at': time.time(),
                'last_activity': time.time()
            }
        return token
    
    def update_activity(self, token):
        with self.locks['sessions']:
            if token in self.sessions:
                self.sessions[token]['last_activity'] = time.time()
                return True
        return False
    
    def remove(self, token):
        with self.locks['sessions']:
            if token in self.sessions:
                del self.sessions[token]
                return True
        return False
    
    def cleanup_expired(self, timeout_seconds=3600):
        now = time.time()
        expired = []
        with self.locks['sessions']:
            for token, session in self.sessions.items():
                if now - session['last_activity'] > timeout_seconds:
                    expired.append(token)
            for token in expired:
                del self.sessions[token]
        return len(expired)

