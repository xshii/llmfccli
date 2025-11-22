#ifndef NETWORK_HANDLER_H
#define NETWORK_HANDLER_H

#include <string>
#include <functional>

class NetworkHandler {
public:
    NetworkHandler();
    ~NetworkHandler();
    
    // Connect to server (missing timeout/retry mechanism for test case 1)
    bool connect(const std::string& host, int port);
    
    // Disconnect from server
    void disconnect();
    
    // Send data
    bool send(const std::string& data);
    
    // Receive data
    std::string receive();
    
    // Check connection status
    bool isConnected() const;
    
    // Set error callback
    void setErrorCallback(std::function<void(const std::string&)> callback);
    
private:
    int sockfd_;
    bool connected_;
    std::function<void(const std::string&)> errorCallback_;
    
    void handleError(const std::string& message);
};

#endif // NETWORK_HANDLER_H
