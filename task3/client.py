import socket
import selectors
import traceback

import ClientSock

sel = selectors.DefaultSelector()

def start_connection(host, port):
    addr = (host, port)
    print(f"Starting connection to {addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    message = ClientSock.Client(host, port, 8001, sel, sock)
    sel.register(sock, events, data=message)


host, port = '127.0.0.1', 8000
for i in range(50):
    start_connection(host, port)

try:
    while True:
        events = sel.select(timeout=1)
        for key, mask in events:
            message = key.data
            try:
                message.process_events(mask)
            except Exception:
                print(
                    f"Main: Error: Exception for {message.host}:\n"
                    f"{traceback.format_exc()}"
                )
                message.close()
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()