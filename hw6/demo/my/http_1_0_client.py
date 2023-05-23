import socket

class HTTPClient:
    def __init__(self):
        pass

    def get(self, url, headers=None, stream=False):
        # Send the request and return the response (Object)
        # url = "http://127.0.0.1:8080/static/xxx.txt"
        # If stream=True, the response should be returned immediately after the full headers have been received.
        host, port, path = self.parse_url(url)

        # Create a socket and connect to the server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(5)  # Set a timeout for socket operations
        client_socket.connect((host, port))

        # Send the GET request
        request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\nContent-Length: 0\r\n\r\n"
        client_socket.sendall(request.encode())

        # Create a Response object to handle the response
        response = Response(client_socket, stream)
        x = response.recv_header()
        if x != 0:
            return None
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


class Response:
    def __init__(self, socket, stream):
        self.socket = socket
        self.stream = stream

        # Fields
        self.version = ""  # e.g., "HTTP/1.0"
        self.status = ""  # e.g., "200 OK"
        self.headers = {}  # e.g., {"content-type": "application/json"}
        self.body = b""  # e.g., b"{'id': '123', 'key':'456'}"
        self.body_length = 0
        self.complete = False
    
    def recv_header(self):
        response = b""
        while b"\r\n\r\n" not in response:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                response += data
            except socket.timeout:
                return 1
        
        status_line, remaining = response.split(b"\r\n", 1)
        self.version, self.status = status_line.decode().split(" ", 1)
        headers, remaining = remaining.split(b"\r\n\r\n", 1)
        header_lines = headers.decode().split("\r\n")
        for line in header_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                self.headers[key] = value
        
        if self.version != "HTTP/1.0" or self.status != "200 OK" or "content-length" not in self.headers:
            return 1
        
        self.body_length = int(self.headers["content-length"])

        if self.body_length > 0:
            self.body = remaining[:min(len(remaining), self.body_length)]
            self.body_length = self.body_length - len(remaining)

        if self.stream == False:
            while self.body_length > 0:
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    self.body += data[:min(len(data), self.body_length)]
                    self.body_length = self.body_length - len(data)
                except socket.timeout:
                    return 1
            if self.body_length <= 0:
                self.complete = True
            else:
                return 1
        return 0

    def get_full_body(self):
        if self.stream or not self.complete:
            print(self.stream, self.complete)
            return None
        return self.body
    
    def get_stream_content(self):
        if not self.stream or self.complete:
            return None
        if self.body != b"":
            content = self.body
            self.body = b""
            return content
        content = self.get_remaining_body()  # recv remaining body data from socket
        return content
    
    def get_remaining_body(self):
        try:
            data = self.socket.recv(40960)
            if not data:
                return None
        except socket.timeout:
            return b""
        data = data[:min(len(data), self.body_length)]
        self.body_length = self.body_length - len(data)
        if self.body_length <= 0:
            self.complete = True
        return data
