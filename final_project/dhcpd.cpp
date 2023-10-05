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

#define BUFFER_SIZE 1024
#define SERVER_PORT 67

using namespace std;

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

enum DHCPMessageType {
    DHCPDISCOVER = 1,
    DHCPOFFER = 2,
    DHCPREQUEST = 3,
    DHCPACK = 5
};

void handleDHCPRequest(int serverSocket) {
    struct sockaddr_in clientAddress;
    socklen_t clientAddressLength = sizeof(clientAddress);

    // Allocate memory for receiving the DHCP message
    DHCPMessage* request = (DHCPMessage*)malloc(sizeof(DHCPMessage));

    ssize_t bytesRead = recvfrom(serverSocket, request, sizeof(DHCPMessage), 0,
                                 (struct sockaddr *)&clientAddress, &clientAddressLength);

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

    // Calculate the actual size of the DHCP message
    size_t messageSize = sizeof(DHCPMessage) + bytesRead - sizeof(DHCPMessage);

    // Reallocate memory to fit the actual size of the DHCP message
    request = (DHCPMessage*)realloc(request, messageSize);

    bytesRead = recvfrom(serverSocket, &(request->options[sizeof(DHCPMessage)]), messageSize - sizeof(DHCPMessage), 0,
                         (struct sockaddr *)&clientAddress, &clientAddressLength);

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
    cout << "Transaction ID: " << request->xid << endl;
    cout << "Seconds: " << request->secs << endl;
    cout << "Flags: " << request->flags << endl;
    cout << "Client IP Address: " << inet_ntoa(*(struct in_addr *)&(request->ciaddr)) << endl;
    cout << "Your IP Address: " << inet_ntoa(*(struct in_addr *)&(request->yiaddr)) << endl;
    cout << "Server IP Address: " << inet_ntoa(*(struct in_addr *)&(request->siaddr)) << endl;
    cout << "Gateway IP Address: " << inet_ntoa(*(struct in_addr *)&(request->giaddr)) << endl;

    cout << "Client MAC Address: ";
    for (int i = 0; i < 6; i++) {
        printf("%02x", request->chaddr[i]);
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

    DHCPMessage* response = (DHCPMessage*)malloc(sizeof(DHCPMessage));
    memset(response, 0, sizeof(DHCPMessage));

    response->op = 2; // Boot reply
    response->htype = 1; // Ethernet
    response->hlen = 6; // MAC address length
    response->xid = request->xid;
    response->yiaddr = htonl(0xC0A80164); // Example: 192.168.1.100
    cout << messageType << '\n';
    if (messageType == DHCPDISCOVER) {
        // DHCPDISCOVER
        // Generate DHCPOFFER
        response->options[0] = 53; // Message type
        response->options[1] = 1; // Length
        response->options[2] = DHCPOFFER;

        // Enable broadcast
        int broadcastEnable = 1;
        setsockopt(serverSocket, SOL_SOCKET, SO_BROADCAST, &broadcastEnable, sizeof(broadcastEnable));

        struct sockaddr_in broadcastAddress;
        memset(&broadcastAddress, 0, sizeof(broadcastAddress));
        broadcastAddress.sin_family = AF_INET;
        broadcastAddress.sin_port = htons(SERVER_PORT);
        broadcastAddress.sin_addr.s_addr = htonl(INADDR_BROADCAST);

        ssize_t bytesSent = sendto(serverSocket, response, sizeof(DHCPMessage), 0,
                                   (struct sockaddr *)&broadcastAddress, sizeof(broadcastAddress));
        cout << bytesSent << '\n';
        if (bytesSent <= 0) {
            cerr << "Error sending DHCPOFFER" << endl;
        }
    } else if (messageType == DHCPREQUEST) {
        // DHCPREQUEST
        // Generate DHCPACK
        response->options[0] = 53; // Message type
        response->options[1] = 1; // Length
        response->options[2] = DHCPACK;

        ssize_t bytesSent = sendto(serverSocket, response, sizeof(DHCPMessage), 0,
                                   (struct sockaddr *)&clientAddress, clientAddressLength);
        cout << bytesSent << '\n';
        if (bytesSent <= 0) {
            cerr << "Error sending DHCPACK" << endl;
        }
    }

    free(request);
    free(response);
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
