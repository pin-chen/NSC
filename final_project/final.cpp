#include <iostream>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <net/if.h>
#include <netinet/if_ether.h>
#include <linux/if_packet.h>
#include <map>
#include <string>
#define BUFFER_SIZE 1024
#define SERVER_PORT 67
using namespace std;

// 192.168.0.0+X
int ip_begin = 100;
int ip_end = 200;
// netmask
uint32_t netmask = 0xFFFFFF00;
// Interface
string interface = "enp0s3";
// Server MAC
unsigned char srcMac[6] = {0x08, 0x00, 0x27, 0x9f, 0x16, 0xc6};
// Server IP
uint32_t serverIP = 0xC0A80001;

map<std::string, int> ip_table;
map<int, bool> ip_used;

struct DHCPMessage {
    uint8_t op;
    uint8_t htype;
    uint8_t hlen;
    uint8_t hops;
    uint32_t xid;
    uint16_t secs;
    uint16_t flags;
    uint32_t ciaddr;
    uint32_t yiaddr;
    uint32_t siaddr;
    uint32_t giaddr;
    uint8_t chaddr[16];
    uint8_t padding[192];
    uint32_t magic_cookie;
    uint8_t options[64];
};

enum DHCPMessageType {
    DHCPDISCOVER = 1,
    DHCPOFFER = 2,
    DHCPREQUEST = 3,
    DHCPACK = 5
};

unsigned short in_cksum(unsigned short *addr, int len) {
    int nleft = len;
    int sum = 0;
    unsigned short *w = addr;
    unsigned short answer = 0;

    // Sum all 16-bit words
    while (nleft > 1) {
        sum += *w++;
        nleft -= 2;
    }

    // Add the padding byte if necessary
    if (nleft == 1) {
        *(unsigned char *)(&answer) = *(unsigned char *)w;
        sum += answer;
    }

    // Add the carry
    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    answer = ~sum;

    return answer;
}

void sendDHCP(unsigned char* dstMac, char ip_s[], DHCPMessage* payload){
    int rawSocket = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (rawSocket == -1) {
        std::cerr << "Failed to create raw socket." << std::endl;
        return;
    }

    // Prepare the Ethernet frame
    struct ethhdr ethernetHeader;
    std::memcpy(ethernetHeader.h_source, srcMac, 6);                        // Source MAC
    std::memcpy(ethernetHeader.h_dest, dstMac, 6);                          // Destination MAC
    ethernetHeader.h_proto = htons(ETH_P_IP);                               // Ethertype

    // Prepare the IP packet
    struct iphdr ipHeader;
    std::memset(&ipHeader, 0, sizeof(struct iphdr));
    ipHeader.version = 4;                                                   // IPv4
    ipHeader.ihl = 5;                                                       // Header length in 32-bit words (5 for no options)
    ipHeader.tos = 0;                                                       // Type of service (0 for default)
    ipHeader.tot_len = htons(sizeof(struct iphdr));                         // Total length of the IP packet
    ipHeader.id = htons(12345); ;                                           // Identification (0 for default)
    ipHeader.frag_off = htons(IP_DF);                                       // Fragment offset (0 for default)
    ipHeader.ttl = 64;                                                      // Time-to-live (64 for default)
    ipHeader.protocol = IPPROTO_UDP;                                        // Protocol (UDP)
    ipHeader.check = 0;                                                     // Checksum (0 for now)
    ipHeader.saddr = inet_addr("192.168.0.1");                              // Source IP address
    ipHeader.daddr = inet_addr(ip_s);                                       // Destination IP address


    struct udphdr udpHeader;
    std::memset(&udpHeader, 0, sizeof(struct udphdr));
    udpHeader.source = htons(67);                                           // Source port
    udpHeader.dest = htons(68);                                             // Destination port
    udpHeader.len = htons(sizeof(struct udphdr));                           // Length of UDP header and payload
    udpHeader.check = 0;                                                    // Checksum (0 for now)

    int payloadLength = sizeof(DHCPMessage);

    ipHeader.tot_len = htons(sizeof(struct iphdr) + sizeof(struct udphdr) + payloadLength);
    ipHeader.check = in_cksum((unsigned short *)&ipHeader, sizeof(struct iphdr));
    udpHeader.len = htons(sizeof(struct udphdr) + payloadLength);

    // Combine the headers and payload into a buffer
    char buffer[sizeof(struct ethhdr) + sizeof(struct iphdr) + sizeof(struct udphdr) + payloadLength];
    std::memcpy(buffer, &ethernetHeader, sizeof(struct ethhdr));
    std::memcpy(buffer + sizeof(struct ethhdr), &ipHeader, sizeof(struct iphdr));
    std::memcpy(buffer + sizeof(struct ethhdr) + sizeof(struct iphdr), &udpHeader, sizeof(struct udphdr));
    std::memcpy(buffer + sizeof(struct ethhdr) + sizeof(struct iphdr) + sizeof(struct udphdr), payload, payloadLength);

    // Send the packet through the raw socket
    struct sockaddr_ll socketAddress;
    std::memset(&socketAddress, 0, sizeof(struct sockaddr_ll));
    socketAddress.sll_family = AF_PACKET;
    socketAddress.sll_protocol = htons(ETH_P_ALL);
    socketAddress.sll_ifindex = if_nametoindex(interface);
    socketAddress.sll_pkttype = PACKET_OTHERHOST;
    socketAddress.sll_halen = ETH_ALEN;
    std::memcpy(socketAddress.sll_addr, dstMac, 6);

    if (sendto(rawSocket, buffer, sizeof(buffer), 0, (struct sockaddr*)&socketAddress, sizeof(socketAddress)) == -1) {
        std::cerr << "Failed to send raw packet." << std::endl;
        return;
    }

    std::cout << "Raw packet sent successfully.\n" << std::endl;

    // Close the raw socket
    close(rawSocket);
}

void handleDHCPRequest(int serverSocket) {
    struct sockaddr_in clientAddress;
    socklen_t clientAddressLength = sizeof(clientAddress);

    // Allocate memory for receiving the DHCP message
    DHCPMessage* request = (DHCPMessage*)malloc(sizeof(DHCPMessage));

    ssize_t bytesRead = recvfrom(serverSocket, request, sizeof(DHCPMessage), 0, (struct sockaddr *)&clientAddress, &clientAddressLength);
    
    cout << "byteRead: " << bytesRead << '\n';
    if (bytesRead <= 0) {
        cerr << "Error receiving DHCP request" << endl;
        free(request);
        return;
    }

    if (request->op != 1 || request->options[0] != 53) {
        cout << "Received non-DHCPDISCOVER or non-DHCPREQUEST message. Ignoring." << endl;
        free(request);
        return;
    }

    DHCPMessageType messageType = (DHCPMessageType)request->options[2];

    if (bytesRead <= 0) {
        cerr << "Error receiving DHCP request" << endl;
        free(request);
        return;
    }

    cout << "DHCP Message Received:" << endl;
    cout << "----------------------" << endl;
    cout << "Operation: " << static_cast<int>(request->op) << endl;
    cout << "Hardware Type: " << static_cast<int>(request->htype) << endl;
    cout << "Hardware Address Length: " << static_cast<int>(request->hlen) << endl;
    cout << "Hops: " << static_cast<int>(request->hops) << endl;
    cout << "Transaction ID: " << std::hex << request->xid << endl;
    cout << "Seconds: " << request->secs << endl;
    cout << "Flags: " << request->flags << endl;
    cout << "Client IP Address: " << inet_ntoa(*(struct in_addr *)&(request->ciaddr)) << endl;
    cout << "Your IP Address: " << inet_ntoa(*(struct in_addr *)&(request->yiaddr)) << endl;
    cout << "Server IP Address: " << inet_ntoa(*(struct in_addr *)&(request->siaddr)) << endl;
    cout << "Gateway IP Address: " << inet_ntoa(*(struct in_addr *)&(request->giaddr)) << endl;

    string tMAC;
    tMAC.resize(12);
    cout << "Client MAC Address: ";
    for (int i = 0; i < 6; i++) {
        printf("%02x", request->chaddr[i]);
        sprintf(&tMAC[i * 2], "%02x", request->chaddr[i]);
        if (i < 5) {
            cout << ":";
        }
    }
    cout << endl;
    
    cout << "Client Hardware Padding: ";
    for (int i = 6; i < 16; i++) {
        printf("%02x", request->chaddr[i]);
        
        if (i < 15) {
            cout << ":";
        }
    }
    cout << endl;

    if (messageType == DHCPDISCOVER) {
        cout << "DHCPDISCOVER\n";
    } else if (messageType == DHCPREQUEST) {
        cout << "DHCPREQUEST\n";
    }
    cout << endl;

    int cur_ip = -1;
    if(ip_table.find(tMAC) != ip_table.end()){
        cur_ip = ip_table[tMAC];
    }else{
        for(int i = ip_begin; i <= ip_end; i += 1){
            if(ip_used.find(i) == ip_used.end()){
                cur_ip = i;
                ip_table[tMAC] = i;
                ip_used[i] = 1;
                break;
            }
        }
    }

    DHCPMessage* response = (DHCPMessage*)malloc(sizeof(DHCPMessage));
    memset(response, 0, sizeof(DHCPMessage));

    response->op = 2; // Boot reply
    response->htype = 1;
    response->hlen = 6;
    response->hops = 0;
    response->xid = request->xid;
    response->secs = htons(0x0000);
    response->flags = htons(0x0000);
    response->ciaddr = htonl(0x0);
    response->yiaddr = htonl(0xC0A80000 + cur_ip);
    response->siaddr = htonl(serverIP);
    response->giaddr = htonl(0x0);
    for(int i = 0; i < 6; i++){
        response->chaddr[i] = request->chaddr[i];
    }
    response->magic_cookie = request->magic_cookie;

    response->options[0] = 53; // Option code
    response->options[1] = 1; // Option length
    // DHCP Server IP: 192.168.0.1
    response->options[3] = 54;
    uint32_t dhcpServerIP = htonl(serverIP);
    response->options[4] = sizeof(dhcpServerIP);
    memcpy(&response->options[5], &dhcpServerIP, sizeof(dhcpServerIP));
    // Subnet mask: 255.255.255.0
    response->options[9] = 1;
    uint32_t subnetMask = htonl(netmask);
    response->options[10] = sizeof(subnetMask);
    memcpy(&response->options[11], &subnetMask, sizeof(subnetMask));
    //
    response->options[15] = 0xff;

    char ip_s[20];
    sprintf(ip_s, "192.168.0.%d", cur_ip);
    if (messageType == DHCPDISCOVER) {
        response->options[2] = 2; // DHCP Offer
        sendDHCP((uint8_t*)request->chaddr, ip_s, response);
    } else if (messageType == DHCPREQUEST) {
        response->options[2] = 5; // DHCP Ack
        sendDHCP((uint8_t*)request->chaddr, ip_s, response);
    }
    free(response);
    free(request);
}

int main() {
    int serverSocket = socket(AF_INET, SOCK_DGRAM, 0);
    if (serverSocket < 0) {
        cerr << "Error creating server socket" << endl;
        return 1;
    }

    int optval = 1;
    setsockopt(serverSocket, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval));

    struct sockaddr_in serverAddress;
    memset(&serverAddress, 0, sizeof(serverAddress));
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_addr.s_addr = INADDR_ANY;
    serverAddress.sin_port = htons(SERVER_PORT);

    if (bind(serverSocket, (struct sockaddr *)&serverAddress, sizeof(serverAddress)) < 0) {
        cerr << "Error binding server socket" << endl;
        close(serverSocket);
        return 1;
    }

    cout << "DHCP server is running on port " << SERVER_PORT << endl;

    while (true) {
        handleDHCPRequest(serverSocket);
    }

    close(serverSocket);
    return 0;
}
