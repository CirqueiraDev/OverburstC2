import http.server
import socketserver
import os
import socket

PORT = 8080
FOLDER = os.path.dirname(os.path.abspath(__file__))
SERVE_DIR = os.path.join(FOLDER, 'binaries')

# Verifica se o diretório existe
if not os.path.exists(SERVE_DIR):
    print(f"[!] Erro: O diretório '{SERVE_DIR}' não existe!")
    exit(1)

os.chdir(SERVE_DIR)

class Handler(http.server.SimpleHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.request.settimeout(60)
    
    def log_message(self, format, *args):
        # Customiza as mensagens de log
        print(f"[{self.log_date_time_string()}] {format % args}")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

local_ip = get_local_ip()

print("=" * 60)
print(f"[+] Servidor iniciado com sucesso!")
print(f"[+] Diretório servido: {SERVE_DIR}")
print(f"[+] Porta: {PORT}")
print("=" * 60)
print(f"[+] Acesse o servidor em:")
print(f"    → http://localhost:{PORT}")
print(f"    → http://127.0.0.1:{PORT}")
print(f"    → http://{local_ip}:{PORT}")
print("=" * 60)
print("[+] Pressione Ctrl+C para parar o servidor")
print("=" * 60)

try:
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n[!] Servidor encerrado pelo usuário")
except Exception as e:
    print(f"\n[!] Erro ao iniciar servidor: {e}")
