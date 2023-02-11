import re
import sys
import socket
import time



from kittens.tui.handler import result_handler
from kitty.key_encoding import KeyEvent, parse_shortcut


def get_nvim_socket(window, vim_id):
    fp = window.child.foreground_processes
    for p in fp:
        if len(p['cmdline']) >= 1 and re.search(vim_id, p['cmdline'][0], re.I):
            try:
                listen_arg_index = p['cmdline'].index('--listen')
            except ValueError:
                continue

            listen_socket_index = listen_arg_index + 1

            if listen_socket_index >= len(p['cmdline']):
                continue

            return p['cmdline'][listen_socket_index]

    return ''

def get_winnr(socket_filename):
    request = b'\x94\x00\x02\xa9nvim_eval\x91\xa7winnr()'
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(socket_filename)
    sock.sendall(request)
    response = sock.recv(4096)
    sock.close()
    winnr = response[4]
    return winnr

def encode_key_mapping(window, key_mapping):
    mods, key = parse_shortcut(key_mapping)
    event = KeyEvent(
        mods=mods,
        key=key,
        shift=bool(mods & 1),
        alt=bool(mods & 2),
        ctrl=bool(mods & 4),
        super=bool(mods & 8),
        hyper=bool(mods & 16),
        meta=bool(mods & 32),
    ).as_window_system_event()

    return window.encoded_key(event)


def main():
    pass


@result_handler(no_ui=True)
def handle_result(args, result, target_window_id, boss):
    window = boss.window_id_map.get(target_window_id)
    direction = args[1]
    key_mapping = args[2]
    vim_id = args[3] if len(args) > 4 else "n?vim"

    if window is None:
        return
    if socket_filename := get_nvim_socket(window, vim_id):
        encoded = encode_key_mapping(window, key_mapping)
        old_winnr = get_winnr(socket_filename)
        window.write_to_child(encoded)
        time.sleep(.030)
        new_winnr = get_winnr(socket_filename)
        if old_winnr == new_winnr:
            boss.active_tab.neighboring_window(direction)
    else:
        boss.active_tab.neighboring_window(direction)

