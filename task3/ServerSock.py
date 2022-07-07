import uuid
import selectors
import struct
import json

class Server:
    def __init__(self, selector, sock, addr, authenticatedUsers):
        self.host = '127.0.0.1'
        self.port = 8000
        self.authPort = 8001
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""
        self.sock = sock
        self.selector = selector
        self.header = None
        self.data_len = None
        self.serverCode  =None
        self.response = None
        self.messageBuffered  = False
        self.request = None
        self.authenticatedUsers = authenticatedUsers

    def _read_raw(self):
        try:
            data = self.sock.recv(1024)
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
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]
                if sent and not self._send_buffer:
                    self.close()

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

    def _process_request(self):
        if len(self._recv_buffer) < self.header:
            return
        data = self._recv_buffer[:self.header]
        self._recv_buffer = self._recv_buffer[self.header:]
        data = json.loads(data.decode('utf-8'))
        self.request = data
        print(f"Received request {self.request!r} from {self.host}: {self.port}")
    

    def read(self):
        self._read_raw()
        if not self.header:
            self._process_header()
        if self.header:
            self._process_request()
            return True
        return False

    def write(self):
        if self.request:
            autchCode = str(uuid.uuid4().fields[-1])[:5]
            id = self.request["id"]
            self.authenticatedUsers[id] = autchCode
            self.createMessage({"authCode": autchCode})
            self.request = None
        self._write_raw()

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()
    

    def close(self):
        print(f"Closing connection to {self.host} {self.port}")
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                f"Error: selector.unregister() exception for "
                f"{self.host}: {e!r}"
            )

        try:
            self.sock.close()
        except OSError as e:
            print(f"Error: socket.close() exception for {self.host}: {e!r}")
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

class AuthServer(Server):
    def __init__(self, selector, sock, addr, authenticatedUsers):
        super().__init__(selector, sock, addr, authenticatedUsers)
        self.host = '127.0.0.1'
        self.port = 8001
        self.isAuthenticated = False

    def appendToFile(self, fileName, data):
        with open(fileName, 'a') as f:
            f.write(data)

    def write(self):
        if self.request:
            if self.isAuthenticated:
                self.createMessage({"UserAuthenticated": "True"})
                self.appendToFile('log.txt', self.request['message'] + '\n')
            else:
                self.createMessage({"error": "User ID does not match authCode", 'UserAuthenticated': "False"})
            self.request = None
        self._write_raw()

    def _process_request(self):
        if len(self._recv_buffer) < self.header:
            return
        data = self._recv_buffer[:self.header]
        self._recv_buffer = self._recv_buffer[self.header:]
        data = json.loads(data.decode('utf-8'))
        self.request = data
        if 'authCode' in self.request:
            if self.authenticatedUsers[data['id']] == data['authCode']:
                self.isAuthenticated = True

        print(f"Received request {self.request!r} from {self.host}: {self.port}")
