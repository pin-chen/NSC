import time
import socket
import threading
import queue
import heapq
import fcntl
import struct

def encode_header(type, packet_num, frame_num, frame_type, stream_id, stream_offset):
    header = type.to_bytes(4, byteorder='big')
    header += packet_num.to_bytes(8, byteorder='big')
    header += frame_num.to_bytes(4, byteorder='big')
    header += frame_type.to_bytes(4, byteorder='big')
    header += stream_id.to_bytes(4, byteorder='big')
    header += stream_offset.to_bytes(8, byteorder='big')
    return header

def decode_header(data):
    type = int.from_bytes(data[:4], byteorder='big')
    packet_num = int.from_bytes(data[4:12], byteorder='big')
    frame_num = int.from_bytes(data[12:16], byteorder='big')
    frame_type = int.from_bytes(data[16:20], byteorder='big')
    stream_id = int.from_bytes(data[20:24], byteorder='big')
    stream_offset = int.from_bytes(data[24:32], byteorder='big')
    return (type, packet_num, frame_num, frame_type, stream_id, stream_offset)

class QUICClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = None
        self.send_thread = None
        self.recv_thread = None

        self.sendQueue = queue.Queue()
        self.recvQueue = queue.Queue()
        self.handleQueue = queue.Queue()
        self.handleRecvQueue = queue.Queue()

        self.ackQueue = []

        self.recv_timeout = 0.5
        self.sending_rate = 0.1

        self.buffersize = 1000000

    def connect(self, socket_addr: tuple[str, int]):
        """connect to the specific server"""
        while True:
            self.server_address = socket_addr
            CHLO = encode_header(type=0, packet_num=0, frame_num=0, frame_type=0, stream_id=0, stream_offset=0)
            
            send_buffer_size = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
            recv_buffer_size = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

            CHLO += send_buffer_size.to_bytes(8, byteorder='big')
            CHLO += recv_buffer_size.to_bytes(8, byteorder='big')
            
            self.sock.sendto(CHLO, self.server_address)
            ack_receied = False
            start_time = time.time()
            self.sock.settimeout(0.01)
            while not ack_receied and time.time() - start_time < self.recv_timeout:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    type, _, _, _, _, _ = decode_header(data)
                    if addr != self.server_address:
                        continue
                    if type == 1:
                        send_buffer_size = int.from_bytes(data[32:40], byteorder='big')
                        recv_buffer_size = int.from_bytes(data[40:48], byteorder='big')
                        ack_receied = True
                    else:
                        self.sock.sendto(CHLO, self.server_address)
                except socket.timeout:
                    pass
            self.sock.settimeout(None)
            if ack_receied:
                break
        
        #self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, recv_buffer_size)
        #self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, send_buffer_size)

        self.send_thread = threading.Thread(target=self.udp_sendto)
        self.send_thread.start()

        self.recv_thread = threading.Thread(target=self.udp_recvfrom)
        self.recv_thread.start()

        self.handle_thread = threading.Thread(target=self.handle)
        self.handle_thread.start()

    def send(self, stream_id: int, data: bytes):
        """call this method to send data, with non-reputation stream_id"""
        #self.sock.sendto(data, self.client_address)
        self.handleQueue.put((stream_id, data))
    
    def recv(self) -> tuple[int, bytes]: # stream_id, data
        """receive a stream, with stream_id"""
        while True:
            if not self.recvQueue.empty():
                return self.recvQueue.get()
    
    def close(self):
        """close the connection and the socket"""
        self.send_thread.join()
        self.recv_thread.join()
        self.handle_thread.join()
        self.sock.close()

    def udp_recvfrom(self):
        while True:
            data, addr = self.sock.recvfrom(1500)
            if addr != self.server_address:
                continue
            #

            #
            type, packet_num, frame_num, frame_type, stream_id, stream_offset = decode_header(data)
            if type == 2:
                self.handleRecvQueue.put((frame_num, frame_type, stream_id, stream_offset, data[32:]))
                header = encode_header(type=3, packet_num=packet_num, frame_num=0, frame_type=0, stream_id=stream_id, stream_offset=0)
                self.sock.sendto(header, self.server_address)
            elif type == 3:
                for i in range(len(self.ackQueue)):
                    _, index, _ = self.ackQueue[i]
                    if index == packet_num:
                        del self.ackQueue[i]
                        break
            elif type == 4:
                self.buffersize = int.from_bytes(data[32:40], byteorder='big')

    def udp_sendto(self):
        i = 0
        while True:
            if self.buffersize < 3000:
                continue

            if len(self.ackQueue) > 0:
                try:
                    start_time, _, packet = heapq.nsmallest(1, self.ackQueue)[0]
                except IndexError:
                    continue
                if  time.time() - start_time > self.recv_timeout:
                    try:
                        heapq.heappop(self.ackQueue)
                    except IndexError:
                        continue
                    frame_num, frame_type, stream_id, stream_offset, data = packet
                    self.sending_rate *= 2.0
                    self.sending_rate += 0.001
                elif not self.sendQueue.empty():
                    frame_num, frame_type, stream_id, stream_offset, data = self.sendQueue.get()
                else:
                    continue
            elif not self.sendQueue.empty():
                frame_num, frame_type, stream_id, stream_offset, data = self.sendQueue.get()
            else:
                continue
            header = encode_header(type=2, packet_num=i, frame_num=frame_num, frame_type=frame_type, stream_id=stream_id, stream_offset=stream_offset)
            self.sock.sendto(header + data, self.server_address)
            self.ackQueue.append( (time.time(), i, (frame_num, frame_type, stream_id, stream_offset, data)) )
            i += 1
            #time.sleep(self.sending_rate)
            self.sending_rate -= 0.0001

    def handle(self):
        stream_num_dict = dict()
        stream_packet_dict = dict()

        stream_recv_dict = dict()
        stream_recv_num_dict = dict()

        start_time = time.time()
        while True:
            if time.time() - start_time > 10.0:
                start_time = time.time()
                header = encode_header(type=4, packet_num=0, frame_num=0, frame_type=1, stream_id=0, stream_offset=0)
                recv_buffer_size = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
                sock_info = fcntl.ioctl(self.sock.fileno(), 0x541B, struct.pack("i", -1))
                recv_buffer_unused = recv_buffer_size - struct.unpack("i", sock_info)[0]
                #self.sock.sendto(header + recv_buffer_unused.to_bytes(8, byteorder='big'), self.server_address)
            
            if not self.handleQueue.empty():
                stream_id, data = self.handleQueue.get()
                if stream_id not in stream_num_dict:
                    stream_num_dict[stream_id] = 0
                    stream_packet_dict[stream_id] = queue.Queue()
                else:
                    stream_num_dict[stream_id] += 1
                chunk_size = 1300
                chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

                num_of_chunks = len(chunks)
                stream_packet_dict[stream_id].put( (stream_num_dict[stream_id], 0, stream_id, 0, num_of_chunks.to_bytes(4, byteorder='big')) )
                for i in range(num_of_chunks):
                    stream_packet_dict[stream_id].put( (stream_num_dict[stream_id], 0, stream_id, i + 1, chunks[i]) )
            
            if self.sendQueue.qsize() < 10:
                for key in stream_packet_dict.keys():
                    if stream_packet_dict[key].qsize() != 0:
                        tmp = stream_packet_dict[key].get()
                        self.sendQueue.put(tmp)

            if not self.handleRecvQueue.empty():
                frame_num, frame_type, stream_id, stream_offset, data = self.handleRecvQueue.get()
                id = (stream_id, frame_num)
                if id not in stream_recv_dict:
                    stream_recv_dict[id] = dict()
                    stream_recv_num_dict[id] = None
                if stream_offset == 0:
                    stream_recv_num_dict[id] = int.from_bytes(data[:4], byteorder='big')
                else:
                    stream_recv_dict[id][stream_offset] = data
                print(str(id) + ":" + str(len(stream_recv_dict[id])))
                if stream_recv_num_dict[id] != None and len(stream_recv_dict[id]) == stream_recv_num_dict[id]:
                    tmp = sorted(stream_recv_dict[id].items())
                    tmp_data = b''
                    for _, frame in tmp:
                        tmp_data += frame
                    
                    self.recvQueue.put((stream_id, tmp_data))
                    stream_recv_dict[id][-1] = b''

# client side
if __name__ == "__main__":
    client = QUICClient()
    client.connect(("127.0.0.1", 30000))
    
    for i in range(7):
        recv_id, recv_data = client.recv()
        print("id: " + str(recv_id))
        print("recv: " + str(len(recv_data)))
    
        if len(recv_data) != 32:
            if recv_data == ("123456789" * 10000).encode():
                print("Correct!")
            else:
                print("Error")
    
    #recv_id, recv_data = client.recv()
    #print(str(recv_id) + " : " + recv_data.decode("utf-8")) # SOME DATA, MAY EXCEED 1500 bytes
    client.send(2, b"Hello Server!")
    client.close()