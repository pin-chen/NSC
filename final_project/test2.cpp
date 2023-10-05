#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/if_ether.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <unistd.h>
#include <linux/if_packet.h>
#include <netinet/udp.h>

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
    uint8_t options[312];
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

int main(int argc, char *argv[]) {
    // Create a raw socket
    int rawSocket = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (rawSocket == -1) {
        std::cerr << "Failed to create raw socket." << std::endl;
        return 1;
    }

    // Source and destination MAC addresses
    unsigned char srcMac[6] = {0x08, 0x00, 0x27, 0x9f, 0x16, 0xc6};
    unsigned char dstMac[6] = {0x08, 0x00, 0x27, 0xdd, 0xaa, 0xaa};

    // Prepare the Ethernet frame
    struct ethhdr ethernetHeader;
    std::memcpy(ethernetHeader.h_source, srcMac, 6);
    std::memcpy(ethernetHeader.h_dest, dstMac, 6);
    ethernetHeader.h_proto = htons(ETH_P_IP);

    // Prepare the IP packet
    struct iphdr ipHeader;
    std::memset(&ipHeader, 0, sizeof(struct iphdr));
    ipHeader.version = 4;                       // IPv4
    ipHeader.ihl = 5;                           // Header length in 32-bit words (5 for no options)
    ipHeader.tos = 0;                            // Type of service (0 for default)
    ipHeader.tot_len = htons(sizeof(struct iphdr));  // Total length of the IP packet
    ipHeader.id = htons(12345); ;                 // Identification (0 for default)
    ipHeader.frag_off = htons(IP_DF);            // Fragment offset (0 for default)
    ipHeader.ttl = 64;                           // Time-to-live (64 for default)
    ipHeader.protocol = IPPROTO_UDP;             // Protocol (UDP)
    ipHeader.check = 0;                          // Checksum (0 for now)
    ipHeader.saddr = inet_addr("192.168.0.1");   // Source IP address
    ipHeader.daddr = inet_addr("192.168.0.4");  // Destination IP address

    // Create a UDP header
    struct udphdr udpHeader;
    std::memset(&udpHeader, 0, sizeof(struct udphdr));

    // Set UDP header fields
    udpHeader.source = htons(67);  // Source port
    udpHeader.dest = htons(68);    // Destination port
    udpHeader.len = htons(sizeof(struct udphdr));  // Length of UDP header and payload
    udpHeader.check = 0;             // Checksum (0 for now)

    // Define the payload
    //const char* payload = "123456789\n123456789\n123456789\n123456789\n123456789\n";
    ///
    DHCPMessage message;
    memset(&message, 0, sizeof(message));
    message.op = 2; // Boot reply
    message.htype = 1; // Ethernet
    message.hlen = 6; // MAC address length
    message.hops = 0;
    message.xid = 12345678; // Transaction ID
    message.secs = htons(0x0000);
    message.flags = htons(0x0000); // Broadcast flag

    message.ciaddr = htonl(0x0);
    // Client IP: 192.168.0.4
    message.yiaddr = htonl(0xC0A80004);
    // DHCP Message Type: DHCP Offer
    message.options[0] = 53; // Option code
    message.options[1] = 1; // Option length
    if(argc == 1){
        message.options[2] = 2; // DHCP Offer
    }else{
        message.options[2] = 5; // DHCP Ack
    }
    // DHCP Server IP: 192.168.0.1
    message.options[3] = 54;
    uint32_t dhcpServerIP = htonl(0xC0A80001);
    message.options[4] = sizeof(dhcpServerIP);
    memcpy(&message.options[5], &dhcpServerIP, sizeof(dhcpServerIP));
    // Subnet mask: 255.255.255.0
    message.options[9] = 1;
    uint32_t subnetMask = htonl(0xFFFFFF00);
    message.options[10] = sizeof(subnetMask);
    memcpy(&message.options[11], &subnetMask, sizeof(subnetMask));
    //
    message.options[15] = 0xff;

    message.magic_cookie = htonl(0x63825363);
    ///
    DHCPMessage* payload = &message;
    ///
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
    socketAddress.sll_ifindex = if_nametoindex("enp0s3");  // Network interface name
    socketAddress.sll_pkttype = PACKET_OTHERHOST;
    socketAddress.sll_halen = ETH_ALEN;
    std::memcpy(socketAddress.sll_addr, dstMac, 6);

    if (sendto(rawSocket, buffer, sizeof(buffer), 0, (struct sockaddr*)&socketAddress, sizeof(socketAddress)) == -1) {
        std::cerr << "Failed to send raw packet." << std::endl;
        return 1;
    }

    std::cout << "Raw packet sent successfully." << std::endl;

    // Close the raw socket
    close(rawSocket);

    return 0;
}
