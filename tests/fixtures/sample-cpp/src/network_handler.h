// network_handler.h
#ifndef NETWORK_HANDLER_H
#define NETWORK_HANDLER_H

#include <string>

class NetworkHandler {
public:
    NetworkHandler();
    bool connect(const std::string& host);
    void disconnect();

private:
    int port;
};

#endif // NETWORK_HANDLER_H
