import sys
import socket
import selectors
import traceback

import ServerSock

sel = selectors.DefaultSelector()
authenticatedUsers = {}

def accept_wrapper(sock):
    message = None
    conn, addr = sock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    port = sock.getsockname()[1]
    if port == 8000:
        message = ServerSock.Server(sel, conn, addr, authenticatedUsers)
    else:
        message = ServerSock.AuthServer(sel, conn, addr, authenticatedUsers)
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=message)




host, port = '127.0.0.1', 8000
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Avoid bind() exception: OSError: [Errno 48] Address already in use
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {(host, port)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

authSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
authSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
authSock.bind((host, 8001))
authSock.listen()
print(f"Listening on {(host, 8001)}")
authSock.setblocking(False)
sel.register(authSock, selectors.EVENT_READ | selectors.EVENT_WRITE, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                message = key.data
                try:
                    message.process_events(mask)
                except Exception:
                    print(
                        f"Main: Error: Exception for {message.host}:\n"
                        f"{traceback.format_exc()}"
                    )
                    message.close()
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()