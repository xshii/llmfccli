#include "network_handler.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>

NetworkHandler::NetworkHandler() 
    : sockfd_(-1), connected_(false), errorCallback_(nullptr) {
}

NetworkHandler::~NetworkHandler() {
    disconnect();
}

bool NetworkHandler::connect(const std::string& host, int port) {
    // TODO: Add timeout and retry mechanism (Test Case 1 will request this)
    
    sockfd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd_ < 0) {
        handleError("Failed to create socket");
        return false;
    }
    
    struct sockaddr_in serverAddr;
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(port);
    
    if (inet_pton(AF_INET, host.c_str(), &serverAddr.sin_addr) <= 0) {
        handleError("Invalid address");
        close(sockfd_);
        sockfd_ = -1;
        return false;
    }
    
    if (::connect(sockfd_, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) < 0) {
        handleError("Connection failed");
        close(sockfd_);
        sockfd_ = -1;
        return false;
    }
    
    connected_ = true;
    return true;
}

void NetworkHandler::disconnect() {
    if (sockfd_ >= 0) {
        close(sockfd_);
        sockfd_ = -1;
    }
    connected_ = false;
}

bool NetworkHandler::send(const std::string& data) {
    if (!connected_) {
        handleError("Not connected");
        return false;
    }
    
    ssize_t sent = ::send(sockfd_, data.c_str(), data.size(), 0);
    if (sent < 0) {
        handleError("Send failed");
        return false;
    }
    
    return true;
}

std::string NetworkHandler::receive() {
    if (!connected_) {
        handleError("Not connected");
        return "";
    }
    
    char buffer[4096];
    ssize_t received = recv(sockfd_, buffer, sizeof(buffer) - 1, 0);
    
    if (received < 0) {
        handleError("Receive failed");
        return "";
    }
    
    buffer[received] = '\0';
    return std::string(buffer);
}

bool NetworkHandler::isConnected() const {
    return connected_;
}

void NetworkHandler::setErrorCallback(std::function<void(const std::string&)> callback) {
    errorCallback_ = callback;
}

void NetworkHandler::handleError(const std::string& message) {
    if (errorCallback_) {
        errorCallback_(message);
    }
}
