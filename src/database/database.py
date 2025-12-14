import json, os, time
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.json')

def load_users():
    with open(DB_PATH, 'r') as f:
        data = json.load(f)
    return data.get("users", [])

def save_users(users):
    with open(DB_PATH, 'w') as f:
        json.dump({"users": users}, f, indent=4)

def add_user(username, password, plan, role, expiry_days):
    users = load_users()
    if any(u['username'] == username for u in users):
        return False  # já existe

    now = datetime.now()
    joined_at = now.strftime("%d/%m/%Y")
    expires_at = (now + timedelta(days=expiry_days)).strftime("%d/%m/%Y")
    
    users.append({
        "username": username,
        "password": password,
        "role": role,
        "plan": plan,
        "attacks_made": 0,
        "joined_at": joined_at,
        "expires_at": expires_at
    })
    save_users(users)
    return True

def remove_user(username):
    users = load_users()
    initial_count = len(users)
    users = [u for u in users if u['username'] != username]
    
    if len(users) < initial_count:
        save_users(users)
        return True
    return False

def get_user(username):
    users = load_users()
    for u in users:
        if u['username'] == username:
            # Verificar se o usuário expirou e atualizar plano se necessário
            if 'expires_at' in u:
                try:
                    expiry_date = datetime.strptime(u['expires_at'], "%d/%m/%Y")
                    if expiry_date < datetime.now() and u['plan'] != 'NoPlan':
                        u['plan'] = 'NoPlan'
                        for i, user in enumerate(users):
                            if user['username'] == username:
                                users[i] = u
                                break
                        save_users(users)

                    days_remaining = (expiry_date - datetime.now()).days
                    u['days_remaining'] = max(days_remaining, 0)

                except (ValueError, TypeError):
                    u['days_remaining'] = None
            else:
                u['days_remaining'] = None

            return u
    return None

def login(username, password):

    users = load_users()
    for user in users:
        if user['username'] == username and user['password'] == password:
            # Verificar se o usuário expirou e atualizar plano para NoPlan se necessário
            if 'expires_at' in user:
                try:
                    expiry_date = datetime.strptime(user['expires_at'], "%d/%m/%Y")
                    if expiry_date < datetime.now() and user['plan'] != 'NoPlan':
                        user['plan'] = 'NoPlan'
                        # Salvar mudanças
                        for i, u in enumerate(users):
                            if u['username'] == username:
                                users[i] = user
                                break
                        save_users(users)
                except (ValueError, TypeError):
                    pass 
            
            return True
    return False  

def update_user_attack_count(username):
    users = load_users()
    for user in users:
        if user['username'] == username:
            user['attacks_made'] = user.get('attacks_made', 0) + 1
            save_users(users)
            return True
    return False

def is_method_allowed(username, method):
    user = get_user(username)
    if not user:
        return False
        
    plan = user.get('plan', 'NoPlan')
    
    plans_path = os.path.join(os.path.dirname(__file__), '..', 'plans', 'plans.json')
    try:
        with open(plans_path, 'r') as f:
            plans_data = json.load(f)
    except:
        return False

    plan_data = plans_data.get('plans', {}).get(plan, {})
    allowed_methods = plan_data.get('allowed_methods', [])
    
    # Remover o ponto do início do método se existir
    if method.startswith('.'):
        method = method[1:]
        
    return method in allowed_methods