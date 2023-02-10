import sys
import socket


request = b'\x94\x00\x02\xa9nvim_eval\x91\xa7winnr()'
socket_filename = '/Users/az/.local/share/nvim/sockets/fastnav.socket'
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(socket_filename)
sock.sendall(request)
response = sock.recv(4096)
winnr = response[4]

