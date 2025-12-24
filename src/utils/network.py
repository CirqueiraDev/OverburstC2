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

def create_server_socket():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return sock

