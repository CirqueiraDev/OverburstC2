import os, json

METHODS_PATH = os.path.join(os.path.dirname(__file__), 'methods.json')

def load_methods():
    with open(METHODS_PATH, 'r') as f:
        data = json.load(f)
    return data.get("methods", {})

def botnetMethodsName(method):
    methods = load_methods()
    if method == 'ALL':
        return methods
    return methods.get(method, "")

def isBotnetMethod(method):
    methods = load_methods()
    return method in methods

