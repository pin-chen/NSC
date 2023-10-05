#include <iostream>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define BUFFER_SIZE 1024
#define SERVER_PORT 12345

int main() {
    int clientSocket = socket(AF_INET, SOCK_DGRAM, 0);
    if (clientSocket < 0) {
        std::cerr << "Error creating client socket" << std::endl;
        return 1;
    }

    int broadcastEnable = 1;
    if (setsockopt(clientSocket, SOL_SOCKET, SO_BROADCAST, &broadcastEnable, sizeof(broadcastEnable)) < 0) {
        std::cerr << "Error enabling broadcast" << std::endl;
        close(clientSocket);
        return 1;
    }

    struct sockaddr_in serverAddress;
    memset(&serverAddress, 0, sizeof(serverAddress));
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_port = htons(SERVER_PORT);
    serverAddress.sin_addr.s_addr = htonl(INADDR_BROADCAST);

    const char *message = "This is a broadcast message";
    ssize_t bytesSent = sendto(clientSocket, message, strlen(message), 0,
                               (struct sockaddr *)&serverAddress, sizeof(serverAddress));

    if (bytesSent < 0) {
        std::cerr << "Error sending broadcast packet" << std::endl;
    } else {
        std::cout << "Broadcast packet sent successfully" << std::endl;
    }

    close(clientSocket);
    return 0;
}
