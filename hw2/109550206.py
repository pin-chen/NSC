from setting import get_hosts, get_switches, get_links, get_ip, get_mac

class packet:
    def __init__(self, protocol, type, dst_mac, src_mac, dst_ip, src_ip):
        self.protocol = protocol
        self.type = type
        self.dst_mac = dst_mac
        self.src_mac = src_mac
        self.dst_ip = dst_ip
        self.src_ip = src_ip

class host:
    def __init__(self, name, ip, mac):
        self.name = name
        self.ip = ip
        self.mac = mac 
        self.port_to = None 
        self.arp_table = dict() # maps IP addresses to MAC addresses
        self.port_to_port_num = -1
    def add(self, node):
        self.port_to = node
        return 0
    def update_link(self, num1, num2):
        self.port_to_port_num = num2
    def show_table(self):
        # display ARP table entries for this host
        print('---------------{}:'.format(self.name))
        for ip, mac in self.arp_table.items():
            print('{} : {}'.format(ip, mac))
    def clear(self):
        # clear ARP table entries for this host
        self.arp_table.clear()
    def update_arp(self, ip, mac):
        # update ARP table with a new entry 
        self.arp_table[ip] = mac
    def handle_packet(self, tmp, port_num): # handle incoming packets
        if tmp.dst_mac != "broadcast_mac" and tmp.dst_mac != self.mac:
            return
        if tmp.dst_ip != self.ip:
            return
        if tmp.protocol == "arp":
            self.update_arp(tmp.src_ip, tmp.src_mac)
            if tmp.type == "request":
                p = packet(protocol="arp", type="reply", dst_mac=tmp.src_mac, src_mac=self.mac, dst_ip=tmp.src_ip, src_ip=self.ip)
                self.send(p)
            elif tmp.type == "reply":
                pass
        elif tmp.protocol == "icmp":
            if tmp.type == "request":
                if tmp.src_ip not in self.arp_table:
                    p = packet(protocol="arp", type="request", dst_mac="broadcast_mac", src_mac=self.mac, dst_ip=tmp.src_ip, src_ip=self.ip)
                    self.send(p)
                p = packet(protocol="icmp", type="reply", dst_mac=self.arp_table[tmp.src_ip], src_mac=self.mac, dst_ip=tmp.src_ip, src_ip=self.ip)
                self.send(p)
            elif tmp.type == "reply":
                pass
    def ping(self, dst_ip): # handle a ping request
        if dst_ip not in self.arp_table:
            p = packet(protocol="arp", type="request", dst_mac="broadcast_mac", src_mac=self.mac, dst_ip=dst_ip, src_ip=self.ip)
            self.send(p)
        p = packet(protocol="icmp", type="request", dst_mac=self.arp_table[dst_ip], src_mac=self.mac, dst_ip=dst_ip, src_ip=self.ip)
        self.send(p)
    def send(self, packet):
        node = self.port_to # get node connected to this host
        node.handle_packet(packet, self.port_to_port_num) # send packet to the connected node

class switch:
    def __init__(self, name, port_n):
        self.name = name
        self.mac_table = dict() # maps MAC addresses to port numbers
        self.port_n = port_n # number of ports on this switch
        self.port_to = [None for i in range(port_n)]
        self.port_to_port_num = [-1 for i in range(port_n)]
    def add(self, node): # link with other hosts or switches
        #self.port_to.append(node)
        for i in range(self.port_n):
            if self.port_to[i] == None:
                self.port_to[i] = node
                return i
        raise RuntimeError('switch add')
    def update_link(self, num1, num2):
        self.port_to_port_num[num1] = num2
    def show_table(self):
        # display MAC table entries for this switch
        print('---------------{}:'.format(self.name))
        for mac, port in self.mac_table.items():
            print('{} : {}'.format(mac, port))
    def clear(self):
        # clear MAC table entries for this switch
        self.mac_table.clear()
    def update_mac(self, mac, port):
        # update MAC table with a new entry
        self.mac_table[mac] = port
    def send(self, idx, packet): # send to the specified port
        node = self.port_to[idx] 
        node.handle_packet(packet, self.port_to_port_num[idx])
    def handle_packet(self, packet, port_num): # handle incoming packets
        self.update_mac(packet.src_mac, port_num)
        if packet.dst_mac not in self.mac_table:
            for i in range(self.port_n):
                if self.port_to[i] == None:
                    continue
                if i == port_num:
                    continue
                self.send(i, packet)
        else:
            i = self.mac_table[packet.dst_mac]
            if i == port_num:
                return
            self.send(i, packet)

def add_link(tmp1, tmp2): # create a link between two nodes
    global host_dict, switch_dict
    if tmp1 in host_dict and tmp2 in switch_dict:
        num1 = host_dict[tmp1].add(switch_dict[tmp2])
        num2 = switch_dict[tmp2].add(host_dict[tmp1])
        host_dict[tmp1].update_link(num1, num2)
        switch_dict[tmp2].update_link(num2, num1)
    elif tmp1 in switch_dict and tmp2 in switch_dict:
        num1 = switch_dict[tmp1].add(switch_dict[tmp2])
        num2 = switch_dict[tmp2].add(switch_dict[tmp1])
        switch_dict[tmp1].update_link(num1, num2)
        switch_dict[tmp2].update_link(num2, num1)
    elif tmp1 in switch_dict and tmp2 in host_dict:
        num1 = switch_dict[tmp1].add(host_dict[tmp2])
        num2 = host_dict[tmp2].add(switch_dict[tmp1])
        switch_dict[tmp1].update_link(num1, num2)
        host_dict[tmp2].update_link(num2, num1)
    else:
        raise RuntimeError('add link')     

def set_topology():
    global host_dict, switch_dict
    hostlist = get_hosts().split(' ')
    switchlist = get_switches().split(' ')
    link_command = get_links()
    ip_dic = get_ip()
    mac_dic = get_mac()
    
    host_dict = dict() # maps host names to host objects
    switch_dict = dict() # maps switch names to switch objects
    
    # ... create nodes and links
    for name in hostlist:
        host_dict[name] = host(name=name, ip=ip_dic[name], mac=mac_dic[name])
    
    for name in switchlist:
        switch_dict[name] = switch(name=name, port_n=8)

    linklist = link_command.split(' ')
    for link in linklist:
        node_name = link.split(',')
        add_link(node_name[0], node_name[1])

def ping(tmp1, tmp2): # initiate a ping between two hosts
    global host_dict, switch_dict
    if tmp1 in host_dict and tmp2 in host_dict : 
        node1 = host_dict[tmp1]
        node2 = host_dict[tmp2]
        node1.ping(node2.ip)
    else : 
        # invalid command
        print('a wrong command')
        #print('Not found host')

def show_table(tmp): # display the ARP or MAC table of a node
    global host_dict, switch_dict
    if tmp == 'all_hosts':
        print('ip : mac')
        for h in host_dict.values():
            h.show_table()
    elif tmp == 'all_switches':
        print('mac : port')
        for s in switch_dict.values():
            s.show_table()
    elif tmp in host_dict:
        print('ip : mac')
        host_dict[tmp].show_table()
    elif tmp in switch_dict:
        print('mac : port')
        switch_dict[tmp].show_table()
    else:
        print("a wrong command")
        #print('Not found host/switch')

def clear(tmp):
    global host_dict, switch_dict
    if tmp in host_dict:
        host_dict[tmp].clear()
    elif tmp in switch_dict:
        switch_dict[tmp].clear()
    else:
        print("a wrong command")
        #print('Not found host/switch')

def run_net():
    while(1):
        command_line = input(">> ")
        # ... handle user commands
        argv = command_line.split(' ')
        argc = len(argv)
        if argc == 3 and argv[1] == 'ping':
            ping(argv[0], argv[2])
        elif argc == 2 and argv[0] == 'show_table':
            show_table(argv[1])
        elif argc == 2 and argv[0] == 'clear':
            clear(argv[1])
        else:
            print('a wrong command')
    
def main():
    set_topology()
    run_net()

if __name__ == '__main__':
    main()