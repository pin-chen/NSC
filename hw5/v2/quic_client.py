import time
import socket
import threading
import queue

BUFFERSIZE = 500000

def encode_header(htype, packet_num, frame_num, stream_id, stream_offset, data):
    header = htype.to_bytes(4, byteorder='big')
    header += packet_num.to_bytes(8, byteorder='big')
    header += frame_num.to_bytes(4, byteorder='big')
    header += stream_id.to_bytes(4, byteorder='big')
    header += stream_offset.to_bytes(8, byteorder='big')
    checksum = 0
    for i in range(len(header)):
        checksum = checksum ^ header[i]
    for i in range(len(data)):
        checksum = checksum ^ data[i]
    header += checksum.to_bytes(1, byteorder='big')
    return header + data

def decode_header(data):
    htype = int.from_bytes(data[:4], byteorder='big')
    packet_num = int.from_bytes(data[4:12], byteorder='big')
    frame_num = int.from_bytes(data[12:16], byteorder='big')
    stream_id = int.from_bytes(data[16:20], byteorder='big')
    stream_offset = int.from_bytes(data[20:28], byteorder='big')
    checksum = int.from_bytes(data[28:29], byteorder='big')
    checksum = 0
    for i in range(len(data)):
        checksum = checksum ^ data[i]
    if checksum != 0:
        return (None, None, None, None, None, None)
    return (htype, packet_num, frame_num, stream_id, stream_offset, data[29:])

class QUICClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = None

        self.send_thread = None
        self.recv_thread = None
        self.handle_thread = None

        self.sendQueue = queue.Queue()
        self.recvQueue = queue.Queue()
        self.handleSendQueue = queue.Queue()
        self.handleRecvQueue = queue.Queue()
        self.handleAckQueue = queue.Queue()

        self.ackTable = dict()

        self.recv_timeout = 0.5
        self.sending_waittime = 0.1

        self.cur_recv_buffer = BUFFERSIZE
        self.buffersize = BUFFERSIZE

    def connect(self, socket_addr: tuple[str, int]):
        self.sock.settimeout(0.5)
        self.server_address = socket_addr
        while True:
            CHLO = encode_header(htype=0, packet_num=0, frame_num=0, stream_id=0, stream_offset=0, data=b'CHLO')
            self.sock.sendto(CHLO, self.server_address)
            try:
                data, addr = self.sock.recvfrom(1500)
                if addr != self.server_address:
                    continue
                htype, packet_num, frame_num, stream_id, stream_offset, data = decode_header(data)
                
                if htype == 1:
                    break
            except socket.timeout:
                continue
        
        self.send_thread = threading.Thread(target=self.udp_sendto)
        self.send_thread.start()

        self.recv_thread = threading.Thread(target=self.udp_recvfrom)
        self.recv_thread.start()

        self.handle_thread = threading.Thread(target=self.handle)
        self.handle_thread.start()

    def send(self, stream_id: int, data: bytes):
        self.handleSendQueue.put((stream_id, data))

    def recv(self) -> tuple[int, bytes]:
        while True:
            if not self.recvQueue.empty():
                tmp = self.recvQueue.get()
                self.cur_recv_buffer += len(tmp[1])
                if self.cur_recv_buffer > BUFFERSIZE:
                    self.cur_recv_buffer = BUFFERSIZE
                return tmp
        
    def close(self):
        self.send_thread.join()
        self.recv_thread.join()
        self.handle_thread.join()
        self.sock.close()

    def udp_recvfrom(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(1500)
            except socket.timeout:
                continue
            if addr != self.server_address:
                continue
            htype, packet_num, frame_num, stream_id, stream_offset, data = decode_header(data)
            if htype == None:
                print("!!!!!!!!!!!")
                continue
            elif htype == 0:
                REJ = encode_header(htype=1, packet_num=0, frame_num=0, stream_id=0, stream_offset=0, data=b'REJ')
                self.sock.sendto(REJ, self.server_address)
                continue
            elif htype == 2:
                self.handleRecvQueue.put((frame_num, stream_id, stream_offset, data))
                ACK = encode_header(htype=3, packet_num=packet_num, frame_num=0, stream_id=stream_id, stream_offset=0, data=b'ACK')
                self.sock.sendto(ACK, self.server_address)
            elif htype == 3:
                if self.ackTable[packet_num][2] == False:
                    self.ackTable[packet_num][2] = True
                    self.sending_waittime = 1500 / (1500 / self.sending_waittime + 1000)
            elif htype == 4:
                self.buffersize = int.from_bytes(data[:8], byteorder='big')

    def udp_sendto(self):
        i = 0
        while True:
            # flow control
            if self.buffersize < 1500:
                continue
            
            k = 0
            prev = -1
            for key in self.ackTable.keys():
                if self.ackTable[key][2]:
                    continue
                if time.time() - self.ackTable[key][1] > self.recv_timeout:
                    self.ackTable[key][1] = time.time()
                    self.sock.sendto(self.ackTable[key][0], self.server_address)
                    if key == prev + 1:
                        k += 1
                    else:
                        k = 0
                    prev = key
                    if k > 1:
                        self.sending_waittime *= 2.0
                        k = 0
                        if self.sending_waittime > 5.0:
                            self.sending_waittime = 5.0
                    time.sleep(self.sending_waittime)

            if self.sendQueue.empty():
                continue
            frame_num, stream_id, stream_offset, data = self.sendQueue.get()
            packet = encode_header(htype=2, packet_num=i, frame_num=frame_num, stream_id=stream_id, stream_offset=stream_offset, data=data)
            self.ackTable[i] = [packet, time.time(), False]
            self.sock.sendto(packet, self.server_address)
                        
            i += 1
            time.sleep(self.sending_waittime)

    def handle(self):
        start_time = time.time()

        stream_num_dict = dict()
        stream_packet_dict = dict()

        stream_recv_dict = dict()
        stream_recv_num_dict = dict()
        while True:
            if time.time() - start_time > 2.0:
                data = self.cur_recv_buffer.to_bytes(8, byteorder='big')
                BUF = encode_header(htype=4, packet_num=0, frame_num=0, stream_id=0, stream_offset=0, data=data)
                self.sock.sendto(BUF, self.server_address)
                start_time = time.time()

            # handle send
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

                stream_packet_dict[stream_id].put( (stream_num_dict[stream_id], stream_id, 0, num_of_chunks.to_bytes(8, byteorder='big')) )
                for i in range(num_of_chunks):
                    stream_packet_dict[stream_id].put( (stream_num_dict[stream_id], stream_id, i + 1, chunks[i]) )
            
            if self.sendQueue.qsize() < 100:
                for i in range(2):
                    for key in stream_packet_dict.keys():
                        if stream_packet_dict[key].qsize() != 0:
                            tmp = stream_packet_dict[key].get()
                            self.sendQueue.put(tmp)
            # handle recv
            if not self.handleRecvQueue.empty():
                frame_num, stream_id, stream_offset, data = self.handleRecvQueue.get()
                id = (stream_id, frame_num)
                if id not in stream_recv_dict:
                    stream_recv_dict[id] = dict()
                    stream_recv_num_dict[id] = None
                if stream_offset == 0:
                    stream_recv_num_dict[id] = int.from_bytes(data[:8], byteorder='big')
                else:
                    stream_recv_dict[id][stream_offset] = data
                if stream_recv_num_dict[id] != None and len(stream_recv_dict[id]) == stream_recv_num_dict[id]:
                    tmp = sorted(stream_recv_dict[id].items())
                    tmp_data = b''
                    flag = False
                    for x, frame in tmp:
                        if x == -1:
                            flag = True
                            break
                        tmp_data += frame
                    if flag:
                        stream_recv_dict.pop(id)
                        stream_recv_dict[id] = dict()
                        stream_recv_dict[id][-1] = b''
                        continue
                    self.recvQueue.put((stream_id, tmp_data))
                    self.cur_recv_buffer -= len(tmp_data)
                    if self.cur_recv_buffer < 0:
                        self.cur_recv_buffer = 0
                    stream_recv_dict.pop(id)
                    stream_recv_dict[id] = dict()
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
            if recv_data == ("1234567890" * 100000).encode():
                print("Correct!")
            else:
                print("Error")
    
    #recv_id, recv_data = client.recv()
    #print(str(recv_id) + " : " + recv_data.decode("utf-8")) # SOME DATA, MAY EXCEED 1500 bytes
    client.send(2, b"Hello Server!")
    client.close()