// network_handler.cpp
#include "network_handler.h"
#include <iostream>

class NetworkHandler {
public:
    NetworkHandler() : port(8080) {}

    bool connect(const std::string& host) {
        std::cout << "Connecting to " << host << ":" << port << std::endl;
        // TODO: Add timeout retry mechanism
        return true;
    }

    void disconnect() {
        std::cout << "Disconnected" << std::endl;
    }

private:
    int port;
};
