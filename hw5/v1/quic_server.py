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

class QUICServer:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_address = None
        self.send_thread = None
        self.recv_thread = None

        self.handle_thread = None

        self.sendQueue = queue.Queue()
        self.recvQueue = queue.Queue()
        self.handleSendQueue = queue.Queue()
        self.handleRecvQueue = queue.Queue()
        
        self.removeQueue = queue.Queue()

        self.ackQueue = []

        self.recv_timeout = 0.5
        self.sending_rate = 0.1

        self.buffersize = 1000000

    def listen(self, socket_addr: tuple[str, int]):
        """this method is to open the socket"""
        self.sock.bind(socket_addr)
        #send_buffer_size = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        #print(f"Current send buffer size: {send_buffer_size}")
    
    def accept(self):
        """this method is to indicate that the client can connect to the server now"""
        while True:
            data, address = self.sock.recvfrom(1024)
            self.client_address = address

            type, _, _, _, _, _ = decode_header(data)

            if type == 0:
                send_buffer_size = int.from_bytes(data[32:40], byteorder='big')
                recv_buffer_size = int.from_bytes(data[40:48], byteorder='big')
                break
        
        tmp = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        if tmp < send_buffer_size:
            send_buffer_size = tmp
        tmp = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        if tmp < recv_buffer_size:
            recv_buffer_size = tmp

        REJ = encode_header(type=1, packet_num=0, frame_num=0, frame_type=0, stream_id=0, stream_offset=0)
        REJ += send_buffer_size.to_bytes(8, byteorder='big')
        REJ += recv_buffer_size.to_bytes(8, byteorder='big')
        self.sock.sendto(REJ, self.client_address)

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
        self.handleSendQueue.put((stream_id, data))
    
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
            if addr != self.client_address:
                continue
            #
            CHLO = encode_header(type=0, packet_num=0, frame_num=0, frame_type=0, stream_id=0, stream_offset=0)
            if data == CHLO:
                REJ = encode_header(type=1, packet_num=0, frame_num=0, frame_type=0, stream_id=0, stream_offset=0)
                self.sock.sendto(REJ, self.client_address)
                continue
            #
            
            type, packet_num, frame_num, frame_type, stream_id, stream_offset = decode_header(data)
            if type == 2:
                self.handleRecvQueue.put((frame_num, frame_type, stream_id, stream_offset, data[32:]))
                header = encode_header(type=3, packet_num=packet_num, frame_num=0, frame_type=0, stream_id=stream_id, stream_offset=0)
                self.sock.sendto(header, self.client_address)
            elif type == 3:
                
                for tmp1, index, tmp2 in self.ackQueue:
                    if index == packet_num:
                        #try:
                        #self.ackQueue.remove((tmp1, index, tmp2))
                        self.removeQueue.put((tmp1, index, tmp2))
                        #except:
                        #    pass
                        self.sending_rate = 1500 / (1500 / self.sending_rate + 1500) 
                        #print(self.sending_rate)
                        break
                while not self.removeQueue.empty():
                    try:
                        self.ackQueue.remove(self.removeQueue.get())
                    except:
                        pass
            elif type == 4:
                self.buffersize = int.from_bytes(data[32:40], byteorder='big')

    def udp_sendto(self):
        i = 0

        tmp_index = list()
        while True:
            print("I")
            if self.buffersize < 1000:
                continue
            print(len(self.ackQueue))
            if len(self.ackQueue) > 0:
                try:
                    start_time, index_1, packet = heapq.nsmallest(1, self.ackQueue)[0]
                    start_time, index, packet = heapq.nsmallest(1, self.ackQueue)[0]
                    if index_1 != index:
                        print("Different")
                except IndexError:
                    continue
                if  time.time() - start_time > self.recv_timeout:
                    #try:
                    #self.ackQueue.remove((start_time, index, packet))
                    #except IndexError:
                    #    pass
                    self.removeQueue.put((start_time, index, packet))

                    frame_num, frame_type, stream_id, stream_offset, data = packet
                    
                    tmp_index.append(index)
                    if len(tmp_index) > 4:
                        del tmp_index[0]
                        check = False
                        for i in range(1, len(tmp_index)):
                            if tmp_index[i] != tmp_index[i-1] + 1:
                                check = True
                                break
                        if not check:
                            self.sending_rate *= 1.5
                            print("_________increase" + str(self.sending_rate))
                            tmp_index = []

                elif not self.sendQueue.empty():
                    frame_num, frame_type, stream_id, stream_offset, data = self.sendQueue.get()
                else:
                    continue
            elif not self.sendQueue.empty():
                frame_num, frame_type, stream_id, stream_offset, data = self.sendQueue.get()
            else:
                continue
            header = encode_header(type=2, packet_num=i, frame_num=frame_num, frame_type=frame_type, stream_id=stream_id, stream_offset=stream_offset)
            self.sock.sendto(header + data, self.client_address)
            self.ackQueue.append( (time.time(), i, (frame_num, frame_type, stream_id, stream_offset, data)) )
            i += 1
            #print("real" + str(self.sending_rate))
            #time.sleep(self.sending_rate) #
            #print("rate: " + str(self.sending_rate))

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
                #self.sock.sendto(header + recv_buffer_unused.to_bytes(8, byteorder='big'), self.client_address)

            if not self.handleSendQueue.empty():
                stream_id, data = self.handleSendQueue.get()
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
                for i in range(5):
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
                if stream_recv_num_dict[id] != None and len(stream_recv_dict[id]) == stream_recv_num_dict[id]:
                    tmp = sorted(stream_recv_dict[id].items())
                    tmp_data = b''
                    for _, frame in tmp:
                        tmp_data += frame
                    
                    self.recvQueue.put((stream_id, tmp_data))
                    stream_recv_dict[id][-1] = b''

# server side
if __name__ == "__main__":
    server = QUICServer()
    server.listen(("", 30000))
    server.accept()
    
    for i in range(6):
        msg = "123456789" * 10000
        tmp =  msg.encode()
        server.send(10 + i, tmp)
        print("id: " + str(10 + i))
        print("send: " + str(len(tmp)))
    
    server.send(1, b"SOME DATA, MAY EXCEED 1500 bytes")
    recv_id, recv_data = server.recv()
    print(str(recv_id) + " : " + recv_data.decode("utf-8")) # Hello Server!
    
    server.close() 