import socket
import time
from collections  import deque
import queue
import threading
from QUIC import quic_client

def encode_http3(type, length, payload):
    if length == None:
        length = len(payload)
    header = type.to_bytes(1, byteorder='big')
    header += length.to_bytes(4, byteorder='big')
    return header + payload

def decode_http3(packet):
    if len(packet) < 5:
        return None
    type = int.from_bytes(packet[:1], byteorder='big')
    length = int.from_bytes(packet[1:5], byteorder='big')
    return type, length, packet[5:]

class HTTPClient(): # For HTTP/2
    def __init__(self) -> None:
        self.client_socket = None
        self.stream_id = 1
        self.response_dict = dict()
        self.send_queue = queue.Queue()

        self.send_thread = threading.Thread(target=self._send)
        self.recv_thread = threading.Thread(target=self._recv)
        self.handle_thread = threading.Thread(target=self._handle)
        self.recv_thread.daemon = True
        self.send_thread.daemon = True
        self.handle_thread.daemon = True

        self.payload_stream = dict()
        self.payload_stream[1] = queue.Queue()
        
    def get(self, url, headers=None):
        # Send the request and return the response (Object)
        # url = "http://127.0.0.1:8080/static/xxx.txt"
        host, port, path = self.parse_url(url)
        if self.client_socket == None:
            self.client_socket = quic_client.QUICClient()
            self.client_socket.drop(5)
            self.client_socket.connect((host, port))
            self.send_thread = threading.Thread(target=self._send)
            self.recv_thread = threading.Thread(target=self._recv)
            self.handle_thread = threading.Thread(target=self._handle)
            self.recv_thread.daemon = True
            self.send_thread.daemon = True
            self.handle_thread.daemon = True
            self.recv_thread.start()
            self.send_thread.start()
            self.handle_thread.start()

        self.send_queue.put((host, port, path, self.stream_id))
        response = Response(self.stream_id)
        self.response_dict[self.stream_id] = response
        self.stream_id += 2
        self.payload_stream[self.stream_id] = queue.Queue()
        return response
    
    def parse_url(self, url):
        if url.startswith("http://"):
            url = url[7:]

        parts = url.split("/", 1)
        host_port = parts[0].split(":")
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 80
        path = "/" + parts[1] if len(parts) > 1 else "/"
        return host, port, path
    
    def _send(self):
        while True:
            if self.client_socket == None:
                return
            if self.send_queue.empty():
                continue
            host, port, path, stream_id = self.send_queue.get()
            header = f":method: GET\r\n"
            header += f":path: {path}\r\n"
            header += f":scheme: http\r\n"
            header += f":authority: {host}:{port}\r\n"
            request = encode_http3(type=1, length=None, payload=header.encode())
            #print(stream_id, len(request) - 5)
            #print(request)
            self.client_socket.send(stream_id, request, end=True)

    def _recv(self):
        while True:
            if self.client_socket == None:
                return
            stream_id, data, flags = self.client_socket.recv()
            if not data:
                print("Socket closed by the server.")
                self.client_socket = None
                return
            self.payload_stream[stream_id].put((data, flags))
            
            
    def _handle(self):
        response = dict()
        while True:
            for stream_id in range(1, self.stream_id, 2):
                if self.payload_stream[stream_id].empty():
                    continue
                data, flags = self.payload_stream[stream_id].get()
                if stream_id not in response:
                    response[stream_id] = data
                else:
                    response[stream_id] += data
            
                if len(response[stream_id]) >= 5:
                    type, length, payload = decode_http3(response[stream_id])
                    if len(payload) == length:
                        response[stream_id] = b""
                    elif len(payload) > length:
                        payload, response[stream_id] = payload[:length], payload[length:]
                    else:
                        continue
                #print("recv", stream_id, len(payload))
                if type == 1:
                    header = payload.decode()
                    header_lines = header.split("\r\n")
                    if len(header_lines) < 1:
                        continue
                    for line in header_lines:
                        pesudo_header = line.split(":")
                        if len(pesudo_header) < 3:
                            continue
                        key = pesudo_header[1].strip().lower()
                        value = pesudo_header[2].strip()
                        self.response_dict[stream_id].headers[key] = value
                elif type == 0:
                    self.response_dict[stream_id].status = "OK"
                    self.response_dict[stream_id].contents.append(payload)
                if flags == 1:
                    self.response_dict[stream_id].status = "OK"
                    self.response_dict[stream_id].complete = True

class Response():
    def __init__(self, stream_id, headers = {}, status = "Not yet"):
        self.stream_id = stream_id
        self.headers = headers
        
        self.status = status
        self.body = b""

        self.contents = deque()
        self.complete = False
        
    def get_headers(self):
        begin_time = time.time()
        while self.status == "Not yet":
            if time.time() - begin_time > 5:
                print("get_headers: Already Time out, but still waitting...")
                begin_time = time.time()
                continue
                return None
        return self.headers
    
    def get_full_body(self): # used for handling short body
        begin_time = time.time()
        while not self.complete:
            if time.time() - begin_time > 5:
                print("get_full_body: Already Time out, but still waitting...")
                begin_time = time.time()
                continue
                return None
        if len(self.body) > 0:
            return self.body
        while len(self.contents) > 0:
            self.body += self.contents.popleft()
        return self.body # the full content of HTTP response body
    
    def get_stream_content(self): # used for handling long body
        begin_time = time.time()
        while len(self.contents) == 0: # contents is a buffer, busy waiting for new content
            if self.complete:# or time.time()-begin_time > 5: # if response is complete or timeout
                #print(time.time(), begin_time)
                return None
            if time.time()-begin_time > 5:
                print("get_stream_content: Already Time out, but still waitting...")
                begin_time = time.time()
                continue
                return None
        content = self.contents.popleft() # pop content from deque
        return content # the part content of the HTTP response body