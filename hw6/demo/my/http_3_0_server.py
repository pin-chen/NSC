import socket
import threading
import os
import random
from QUIC import quic_server
import time

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
        self.server_socket = quic_server.QUICServer()
        self.server_socket.listen((self.ip, self.port))
        print(f"Server is running on {self.ip}:{self.port}")

        self.running = True
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def _run_server(self):
        while self.running:
            try:
                self.server_socket.accept()
                print(f"Connection established with ?:?")
                handle_threads = self.recv_request(self.server_socket)
                for handle_thread in handle_threads:
                    handle_thread.join()
                self.server_socket.close()
            except:
                print("Accept error, please check client is not running and retry.")
                break

    def recv_request(self, client_socket):
        x = False
        payload_stream = dict()
        request_stream = dict()
        handle_threads = list()
        while True:
            if x == False:
                try:
                    #print("recving...")
                    stream_id, data, flags = client_socket.recv()
                    #print(stream_id, "-----------")
                except:
                    return handle_threads
                if not data:
                    print("Socket closed by the client.")
                    return handle_threads

                if stream_id not in payload_stream:
                    payload_stream[stream_id] = data
                else:
                    payload_stream[stream_id] += data

            request = payload_stream[stream_id]
            x = False
            if len(data) >= 5:
                type, length, payload = decode_http3(request)
                if len(payload) == length:
                    payload_stream[stream_id] = b""
                elif len(payload) > length:
                    payload, payload_stream[stream_id] = payload[:length], payload[length:]
                    x = True
                else:
                    continue
            #print(stream_id, len(payload))
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
                print(f"Start handle request of stream id: {stream_id}, at {time.time()}")
                handle_thread.start()
                handle_threads.append(handle_thread)
        return handle_threads

    def _handle_request(self, client_socket, pesudo_headers, stream_id):
        time.sleep(1)
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
        response = encode_http3(type=1, length=None, payload=f":status: {status}\r\n".encode())
        #print("send" ,stream_id, len(response) - 5)
        client_socket.send(stream_id, response, end=True)

    def send_directory_response(self, client_socket, stream_id):
        if self.static_path:
            files = os.listdir(self.static_path)
            random_files = random.sample(files, min(3, len(files)))
            response_body = "<html>\n    <header>\n    </header>\n    <body>\n"
            for file in random_files:
                response_body += f"        <a href=\"/static/{file}\">{file}</a>\n"
            response_body += "    </body>\n</html>"
            response = encode_http3(type=1, length=None, payload=f":status: 200 OK\r\n:content-type: text/html\r\n".encode())
            #print("send" ,stream_id, len(response) - 5)
            client_socket.send(stream_id, response)
            response = encode_http3(type=0, length=None, payload=response_body.encode())
            #print("send" ,stream_id, len(response) - 5)
            client_socket.send(stream_id, response, end=True)
        else:
            self.send_text_response(client_socket, "404 Not Found", stream_id)

    def send_file_response(self, client_socket, file_path, stream_id):
        if os.path.exists(file_path) and os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            with open(file_path, "rb") as file:
                response = encode_http3(type=1, length=None, payload=f":status: 200 OK\r\n:content-type: application/octet-stream\r\n".encode())
                #print("send" ,stream_id, len(response) - 5)
                client_socket.send(stream_id, response)
                while True:
                    chunk = file.read(4096)
                    if not chunk:
                        break
                    response = encode_http3(type=0, length=None, payload=chunk)
                    #print("send" ,stream_id, len(response) - 5)
                    client_socket.send(stream_id, response)
                response = encode_http3(type=0, length=0, payload=b"")
                #print("send" ,stream_id, len(response) - 5)
                time.sleep(1)
                client_socket.send(stream_id, response, end=True)
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
            #try:
            #    dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #    dummy_socket.connect((self.ip, self.port))
            #    dummy_socket.close()
            #except:
            #    pass
            # self.server_socket.shutdown(socket.SHUT_RDWR)  # Shut down the server socket
            self.server_socket.close()
            print("Server socket closed.")

        #if self.server_thread:
        #    self.server_thread.join()
        #    print("Server thread stopped.")

