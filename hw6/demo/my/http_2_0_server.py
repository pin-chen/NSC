import socket
import threading
import os
import random

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
    length = int.from_bytes(packet[:3], byteorder='big')
    type = int.from_bytes(packet[3:4], byteorder='big')
    flags = int.from_bytes(packet[4:5], byteorder='big')
    stream_id = int.from_bytes(packet[5:9], byteorder='big')
    return length, type, flags, stream_id, packet[9:]

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
                handle_threads = self.recv_request(client_socket)
                for handle_thread in handle_threads:
                    handle_thread.join()
                client_socket.close()
            except socket.error:
                break

    def recv_request(self, client_socket):
        handle_threads = list()
        request_stream = dict()
        remaing_data = None
        while True:
            request = b""
            while True:
                if remaing_data == None:
                    try:
                        data = client_socket.recv(4096)
                        if not data:
                            print("Socket closed by the client.")
                            return handle_threads
                    except socket.timeout:
                        continue
                    request += data
                else:
                    request += remaing_data
                    remaing_data = None
                if len(request) >= 9:
                    length, type, flags, stream_id, payload = decode_http2(request)
                    if len(payload) == length:
                        break
                    elif len(payload) > length:
                        payload, remaing_data = payload[:length], payload[length:]
                        break
            
            if stream_id not in request_stream:
                request_stream[stream_id] = dict()

            header = payload.decode()
            header_lines = header.split("\r\n")

            if type != 1 or len(header_lines) < 1:
                continue
            
            for line in header_lines:
                pesudo_header = line.split(":")
                if len(pesudo_header) < 3:
                    continue
                key = pesudo_header[1].strip().lower()
                value = pesudo_header[2].strip()
                request_stream[stream_id][key] = value
            
            if flags == 1:
                pseudo_headers = request_stream.pop(stream_id)
                handle_thread = threading.Thread(target=self._handle_request, args=(client_socket, pseudo_headers, stream_id,))
                handle_thread.start()
                handle_threads.append(handle_thread)
        return handle_threads

    def _handle_request(self, client_socket, pesudo_headers, stream_id):
        try:
            method = pesudo_headers["method"]
            path = pesudo_headers["path"]
            scheme = pesudo_headers["scheme"]
            authority = pesudo_headers["authority"]
        except:
            self.send_text_response(client_socket, "400 Bad Request", stream_id)
            return

        if scheme != "http":
            self.send_text_response(client_socket, "505 HTTP Version Not Supported", stream_id)
            return

        if method == "GET":
            if path == "/":
                self.send_directory_response(client_socket, stream_id)
            elif path.startswith("/static/") and self.static_path:
                file_path = os.path.join(self.static_path, path[8:])
                self.send_file_response(client_socket, file_path, stream_id)
            else:
                self.send_text_response(client_socket, "404 Not Found", stream_id)
        else:
            self.send_text_response(client_socket, "405 Method Not Allowed", stream_id)

    def send_text_response(self, client_socket, status, stream_id):
        response = encode_http2(length=None, type=1, flags=1, stream_id=stream_id, payload=f":status: {status}\r\n".encode())
        #print(status, len(response), stream_id)
        client_socket.sendall(response)

    def send_directory_response(self, client_socket, stream_id):
        if self.static_path:
            files = os.listdir(self.static_path)
            random_files = random.sample(files, min(3, len(files)))
            response_body = "<html>\n    <header>\n    </header>\n    <body>\n"
            for file in random_files:
                response_body += f"        <a href=\"/static/{file}\">{file}</a>\n"
            response_body += "    </body>\n</html>"
            response = encode_http2(length=None, type=1, flags=0, stream_id=stream_id, payload=f":status: 200 OK\r\n:content-type: text/html\r\n".encode())
            #print("dir",len(response), stream_id)
            client_socket.sendall(response)
            response = encode_http2(length=None, type=0, flags=1, stream_id=stream_id, payload=response_body.encode())
            #print("dir",len(response), stream_id)
            client_socket.sendall(response)
        else:
            self.send_text_response(client_socket, "404 Not Found", stream_id)

    def send_file_response(self, client_socket, file_path, stream_id):
        if os.path.exists(file_path) and os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            with open(file_path, "rb") as file:
                response = encode_http2(length=None, type=1, flags=0, stream_id=stream_id, payload=f":status: 200 OK\r\n:content-type: application/octet-stream\r\n".encode())
                #print("file", len(response), stream_id)
                client_socket.sendall(response)
                while True:
                    chunk = file.read(4096)
                    if not chunk:
                        break
                    response = encode_http2(length=None, type=0, flags=0, stream_id=stream_id, payload=chunk)
                    #print("x", len(response), stream_id)
                    client_socket.sendall(response)
                response = encode_http2(length=0, type=0, flags=1, stream_id=stream_id, payload=b"")
                #print("end", len(response), stream_id)
                client_socket.sendall(response)
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

