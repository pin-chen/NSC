import socket
import threading
import os
import random

class HTTPServer():
    def __init__(self, host="127.0.0.1", port=8080):
        self.ip = host
        self.port = port
        self.static_path = None
        self.server_socket = None
        self.server_thread = None
        self.running = False

    def run(self):
        # Create the server socket and start accepting connections.
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(1)
        print(f"Server is running on {self.ip}:{self.port}")

        self.running = True
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def _run_server(self):
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"Connection established with {client_address[0]}:{client_address[1]}")
                client_socket.settimeout(5)
                self.handle_request(client_socket)
                client_socket.close()
            except socket.error:
                break

    def handle_request(self, client_socket):
        request = b""
        while b"\r\n\r\n" not in request:
            try:
                data = client_socket.recv(4096)
                if not data:
                    print("Socket closed by the client.")
                    return
                request += data
            except socket.timeout:
                self.send_text_response(client_socket, "400 Bad Request", "Bad Request")
                return

        request = request.decode()
        request_lines = request.split("\r\n")

        if len(request_lines) < 1 or len(request_lines[0].split()) != 3:
            self.send_text_response(client_socket, "400 Bad Request", "Bad Request")
            return

        method, path, protocol = request_lines[0].split()

        if protocol != "HTTP/1.0":
            self.send_text_response(client_socket, "505 HTTP Version Not Supported", "HTTP Version Not Supported")
            return

        if method == "GET":
            if path == "/":
                self.send_directory_response(client_socket)
            elif path.startswith("/static/") and self.static_path:
                file_path = os.path.join(self.static_path, path[8:])
                self.send_file_response(client_socket, file_path)
            else:
                self.send_text_response(client_socket, "404 Not Found", "Not Found")
        else:
            self.send_text_response(client_socket, "405 Method Not Allowed", "Method Not Allowed")


    def send_text_response(self, client_socket, status, message):
        response = f"HTTP/1.0 {status}\r\nContent-Type: text/plain\r\nContent-Length: {len(message)}\r\n\r\n{message}"
        client_socket.sendall(response.encode())

    def send_directory_response(self, client_socket):
        if self.static_path:
            files = os.listdir(self.static_path)
            random_files = random.sample(files, min(3, len(files)))
            response_body = "<html>\n    <header>\n    </header>\n    <body>\n"
            for file in random_files:
                response_body += f"        <a href=\"/static/{file}\">{file}</a>\n"
            response_body += "    </body>\n</html>"
            content_length = len(response_body)
            response = f"HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nContent-Length: {content_length}\r\n\r\n{response_body}"
            client_socket.sendall(response.encode())
        else:
            self.send_text_response(client_socket, "404 Not Found", "Not Found")

    def send_file_response(self, client_socket, file_path):
        if os.path.exists(file_path) and os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            with open(file_path, "rb") as file:
                response_header = f"HTTP/1.0 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {file_size}\r\n\r\n"
                client_socket.sendall(response_header.encode())
                while True:
                    chunk = file.read(4096)
                    if not chunk:
                        break
                    client_socket.sendall(chunk)
        else:
            self.send_text_response(client_socket, "404 Not Found", "File Not Found")

    def set_static(self, path):
        # Set the static directory so that when the client sends a GET request to the resource "/static/<file_name>",
        # the file located in the static directory is sent back in the response.
        self.static_path = path

    def close(self):
        # Close the server socket and stop the server thread gracefully.
        if self.server_socket:
            self.running = False
            # Create a dummy connection to break the accept() blocking call
            try:
                dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                dummy_socket.connect((self.ip, self.port))
                dummy_socket.close()
            except:
                pass
            # self.server_socket.shutdown(socket.SHUT_RDWR)  # Shut down the server socket
            self.server_socket.close()
            print("Server socket closed.")

        if self.server_thread:
            self.server_thread.join()
            print("Server thread stopped.")

