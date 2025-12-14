import http.server
import socketserver
import os

PORT = 8080

FOLDER = os.path.dirname(os.path.abspath(__file__))
SERVE_DIR = os.path.join(FOLDER, 'compiled-bots')
os.chdir(SERVE_DIR)

class Handler(http.server.SimpleHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.request.settimeout(60)

print(f"[+] Started server on http://0.0.0.0:{PORT}")
print(f"[+] files on: {SERVE_DIR}")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
