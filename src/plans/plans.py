import os, json, ipaddress
from datetime import datetime

PLANS_PATH = os.path.join(os.path.dirname(__file__), 'plans.json')

def load_plans():
    """Carrega informações sobre os planos disponíveis"""
    try:
        with open(PLANS_PATH, 'r') as f:
            data = json.load(f)
        return data.get("plans", {})
    except FileNotFoundError:
        return {}

def get_plan_methods(plan_name):
    """Retorna os métodos disponíveis para um plano específico"""
    plans = load_plans()
    plan = plans.get(plan_name.lower(), plans.get("NoPlan", {}))
    return plan.get("allowed_methods", [])

def validate_plan_for_method(plan_name, method):
    """
    Verifica se um método está disponível para o plano
    """
    if method.startswith('.'):
        method = method[1:]
    
    allowed_methods = get_plan_methods(plan_name)
    return method in allowed_methods

def upgrade_plan(current_plan):
    """
    Retorna o próximo nível de plano baseado no plano atual
    """
    plan_hierarchy = ["NoPlan", "basic", "premium", "vip"]
    try:
        current_index = plan_hierarchy.index(current_plan.lower())
        if current_index < len(plan_hierarchy) - 1:
            return plan_hierarchy[current_index + 1]
    except ValueError:
        pass
    
    return current_plan  # Retorna o mesmo plano se já for o maior ou desconhecido

def get_plan_limitations():
    """
    Retorna um resumo das limitações de cada plano para exibição
    """
    plans = load_plans()
    plan_limits = {}
    
    for plan_name, plan_data in plans.items():
        methods = plan_data.get("allowed_methods", [])
        plan_limits[plan_name] = {
            "methods_count": len(methods),
            "methods": methods
        }
    
    return plan_limits

def format_plan_info(plan_name):
    """
    Formata informações sobre um plano para exibição
    """
    plans = load_plans()
    plan = plans.get(plan_name.lower(), None)
    
    if not plan:
        return f"Plan '{plan_name}' not found"
        
    methods = plan.get("allowed_methods", [])
    
    result = f"Plan: {plan_name.upper()}\n"
    result += f"Available Methods: {len(methods)}\n"
    
    if methods:
        result += "Methods:\n"
        for method in methods:
            result += f" - {method}\n"
    else:
        result += "No methods available for this plan.\n"
        
    return result