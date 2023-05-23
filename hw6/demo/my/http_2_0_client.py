import socket
import time
from collections  import deque
import queue
import threading

def encode_http2(length, type, flags, stream_id, payload):
    if length == None:
        length = len(payload)
    header = length.to_bytes(3, byteorder='big')
    header += type.to_bytes(1, byteorder='big')
    header += flags.to_bytes(1, byteorder='big')
    header += stream_id.to_bytes(4, byteorder='big')
    return header + payload

def decode_http2(packet):
    if len(packet) < 9:
        return None
    #print("__: ", packet[:3])
    length = int.from_bytes(packet[:3], byteorder='big')
    type = int.from_bytes(packet[3:4], byteorder='big')
    flags = int.from_bytes(packet[4:5], byteorder='big')
    stream_id = int.from_bytes(packet[5:9], byteorder='big')
    return length, type, flags, stream_id, packet[9:]

class HTTPClient(): # For HTTP/2
    def __init__(self) -> None:
        self.client_socket = None
        self.stream_id = 1
        self.response_dict = dict()
        self.send_queue = queue.Queue()

        self.send_thread = threading.Thread(target=self._send)
        self.recv_thread = threading.Thread(target=self._recv)
        self.recv_thread.daemon = True
        self.send_thread.daemon = True
        
    def get(self, url, headers=None):
        # Send the request and return the response (Object)
        # url = "http://127.0.0.1:8080/static/xxx.txt"
        host, port, path = self.parse_url(url)
        if self.client_socket == None:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)
            self.client_socket.connect((host, port))
            self.send_thread = threading.Thread(target=self._send)
            self.recv_thread = threading.Thread(target=self._recv)
            self.recv_thread.daemon = True
            self.send_thread.daemon = True
            self.recv_thread.start()
            self.send_thread.start()

        self.send_queue.put((host, port, path, self.stream_id))
        response = Response(self.stream_id)
        self.response_dict[self.stream_id] = response
        self.stream_id += 2
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
            request = encode_http2(length=None, type=1, flags=1, stream_id=stream_id, payload=header.encode())
            self.client_socket.sendall(request)

    def _recv(self):
        #response_stream = dict()
        remaing_data = None
        while True:
            if self.client_socket == None:
                return
            
            response = b""
            while True:
                if remaing_data == None:
                    try:
                        data = self.client_socket.recv(40960)
                        if not data:
                            print("Socket closed by the server.")
                            self.client_socket = None
                            return
                    except socket.timeout:
                        continue
                    response += data
                else:
                    response += remaing_data
                    remaing_data = None

                if len(response) >= 9:
                    length, type, flags, stream_id, payload = decode_http2(response)
                    if len(payload) == length:
                        break
                    elif len(payload) > length:
                        payload, remaing_data = payload[:length], payload[length:]
                        break
            
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
                    #response_stream[stream_id][key] = value
                    self.response_dict[stream_id].headers[key] = value
            elif type == 0:
                self.response_dict[stream_id].status = "OK"
                self.response_dict[stream_id].contents.append(payload)
                """
                if "payload" not in response_stream[stream_id]:
                    response_stream[stream_id]["payload"] = response
                else:
                    response_stream[stream_id]["payload"] += response
                """
            if flags == 1:
                self.response_dict[stream_id].status = "OK"
                #pseudo_headers = response_stream.pop(stream_id)
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
                return None
        return self.headers
    
    def get_full_body(self): # used for handling short body
        begin_time = time.time()
        while not self.complete:
            if time.time() - begin_time > 5:
                return None
        if len(self.body) > 0:
            return self.body
        while len(self.contents) > 0:
            self.body += self.contents.popleft()
        return self.body # the full content of HTTP response body
    
    def get_stream_content(self): # used for handling long body
        begin_time = time.time()
        while len(self.contents) == 0: # contents is a buffer, busy waiting for new content
          if self.complete or time.time()-begin_time > 5: # if response is complete or timeout
              return None
        content = self.contents.popleft() # pop content from deque
        return content # the part content of the HTTP response body