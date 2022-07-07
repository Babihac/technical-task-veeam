import uuid
import socket
import selectors
import types
import struct
import json
import random

class Client:
    def __init__(self, host, port, authPort, selector, sock):
        self.host = host
        self.port = port
        self.authPort = authPort
        self._recv_buffer = b""
        self._send_buffer = b""
        self.sock = sock
        self.selector = selector
        self.header = None
        self.id = str(uuid.uuid4().fields[-1])[:5]
        self.data_len = None
        self.authCode  =None
        self.response = None
        self.messageBuffered  = False
        self.payload = {"id": self.id}
        self.authSocket = None
        self.activeSocket = sock

 

    def _read_raw(self):
        try:
            data = self.activeSocket.recv(1024)
        except BlockingIOError:
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")

    def _write_raw(self):
        if self._send_buffer:
            print(f"Sending {self._send_buffer!r} to {self.host} {self.port}")
            try:
                sent = self.activeSocket.send(self._send_buffer)
            except BlockingIOError:
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]

    def createMessage(self, message):
        data = json.dumps(message).encode('utf-8')
        self._send_buffer = struct.pack("!Q", len(data)) + data
        self.messageBuffered = True

    def _process_header(self):
        HEADER = 8
        if len(self._recv_buffer) < HEADER:
            return
        self.header = struct.unpack("!Q", self._recv_buffer[:HEADER])[0]
        self._recv_buffer = self._recv_buffer[HEADER:]

    def _process_response(self):
        if len(self._recv_buffer) < self.header:
            return
        data = self._recv_buffer[:self.header]
        self._recv_buffer = self._recv_buffer[self.header:]
        data = json.loads(data.decode('utf-8'))
        print(f"Received response {data!r} from {self.host}: {self.port}")
        if 'authCode' in data:
            self.authCode = data['authCode']
            self.authenticate()
        if 'userAuthenticated' in data:
            self.close()

    def read(self):
        self._read_raw()
        if not self.header:
            self._process_header()
        if self.header:
            self._process_response()
            return True
        return False

    def write(self):
        if not self.messageBuffered:
            self.createMessage(self.payload)
        self._write_raw()

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    def authenticate(self):
        self.createAuthSocket()
        self.port = self.authPort
        self.header = None
        self.payload = {"id": self.id, "authCode": self.authCode, 'message': 'user id ' + self.id}
        self.messageBuffered = False

    def createAuthSocket(self):
        self.selector.unregister(self.activeSocket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex((self.host, self.authPort))
        self.activeSocket = sock
        print("Auth socket: ", self.activeSocket)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.selector.register(sock, events, data=self)

    def close(self):
        print(f"Closing connection to {self.host} {self.port}")
        try:
            self.selector.unregister(self.activeSocket)
        except Exception as e:
            print(
                f"Error: selector.unregister() exception for "
                f"{self.host}: {e!r}"
            )

        try:
            self.activeSocket.close()
            self.sock.close()
        except OSError as e:
            print(f"Error: socket.close() exception for {self.host}: {e!r}")
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None
            self.activeSocket = None
    