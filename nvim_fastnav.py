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
    sock.settimeout(.1)
    try:
        sock.connect(socket_filename)
        sock.sendall(request)
        response = sock.recv(4096)
        winnr = response[4]
    except socket.timeout:
        winnr = 0

    sock.close()
    return winnr

def encode_key_mappings(window, key_mappings):
    events = []
    for key_mapping in key_mappings:
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

        events.append(window.encoded_key(event))

    return events


def main():
    pass


@result_handler(no_ui=True)
def handle_result(args, result, target_window_id, boss):
    window = boss.window_id_map.get(target_window_id)
    command = args[1]
    key_mappings = args[2].split(',')
    vim_id = args[3] if len(args) > 4 else "n?vim"

    if window is None:
        return

    if command.startswith('neighboring_window_'):
        direction = command[len('neighboring_window_'):]

        if socket_filename := get_nvim_socket(window, vim_id):
            encoded_key_events = encode_key_mappings(window, key_mappings)
            old_winnr = get_winnr(socket_filename)
            for eke in encoded_key_events:
                window.write_to_child(eke)
            time.sleep(.030)
            new_winnr = get_winnr(socket_filename)
            if old_winnr == new_winnr:
                boss.active_tab.neighboring_window(direction)
        else:
            boss.active_tab.neighboring_window(direction)
    elif command == 'close_window_with_confirmation':
        if socket_filename := get_nvim_socket(window, vim_id):
            encoded_key_events = encode_key_mappings(window, key_mappings)
            for eke in encoded_key_events:
                window.write_to_child(eke)
        else:
            boss.close_window_with_confirmation(ignore_shell = True)
