# NSC

### HW1 Simple tcpdump
- Capture and Filter Packets from a Network Interface.
- Usage:
```
cd hw1 && make
./main -h
  --interface {interface}, -i {interface}
  --count {number}, -c {number}
  --filter {udp, tcp, icmp, all}, -f {udp, tcp, icmp, all}
```
### HW2 Learning Bridge Protocol Simulation
- Behavior of switch when ping.
- ICMP
- ARP
- Test:
```
// Generate TEST command
python generate_cmd.py > cmd.txt
// Run
python 109550206.py < cmd.txt
```
### HW3 Aloha, Slotted Aloha, CSMA, and CSMA/CD protocols Simulation
- The channel efficiency of the Aloha, Slotted Aloha, CSMA, and CSMA/CD protocols under different operation conditions.
- Test:
```
python test.py
```
### HW4 RIP and OSPF Protocols Simulation
- Show path cost and log when learning
- Test:
```
Go test.ipynb
run all
```
### HW5 Reliable UDP as QUIC
- Error Control
- Flow Control
- Congestion Control
- Test:
```
// Some environment setup
sudo tc qdisc show dev lo
sudo tc qdisc add dev lo root netem loss 5%
sudo tc qdisc change dev lo root netem rate 10Mbit
sudo tc qdisc del dev lo root netem rate 10Mbit
// Run
python quic_server.py
python quic client.py
```
### HW6 HTTP 1.0, 1.1, 2.0 and 3.0 Implementaion
- header format
- 1.0 Multiple Connections V.S. 1.1 Persistent Connection
- 1.1 No Pipelining V.S. 2.0 Piplining
- 2.0 TCP V.S. 3.0 QUIC/UDP Stream
- Test:
```
python demo/http_X_X_server_demo.py
python demo/http_X_X_client_demo.py
```
### HW7 SDN with Ryu
- Behavior of switch when ping.
- Build tunnel though switch in different VM.

### Final Project Do anything related to Network.
- DHCP Server Implementaion
- Test environment:
```
Server: Ubuntu 22.04
Client1: Ubuntu 22.04
Client2: CentOS 8 Stream
Client3: Windows 11
```
- Usage:
```
// Run on server and setup interface to LAN with client 
cd final_project
g++ dhcpd.cpp -o dhcpd
sudo ./dhcpd
```
