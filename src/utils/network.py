import socket
import ssl
import logging

def safe_recv(client, max_size, default_max=1024):
    try:
        data = client.recv(min(max_size, default_max))
        if len(data) > max_size:
            return None
        return data
    except:
        return None

def setup_ssl_socket(sock, server_config):
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        cert_file = server_config.get("cert_file", None)
        key_file = server_config.get("key_file", None)
        if cert_file and key_file:
            import os
            if os.path.exists(cert_file) and os.path.exists(key_file):
                context.load_cert_chain(cert_file, key_file)
                return context.wrap_socket(sock, server_side=True)
    except Exception as e:
        logging.warning(f"SSL setup failed: {e}")
    return sock

def create_server_socket(host, port):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock

