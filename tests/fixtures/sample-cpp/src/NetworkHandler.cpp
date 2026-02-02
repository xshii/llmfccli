#include "NetworkHandler.h"
#include <iostream>
#include <thread>
#include <atomic>

namespace network {

struct NetworkHandler::Impl {
    std::atomic<bool> asyncRunning{false};
    std::thread asyncThread;
};

NetworkHandler::NetworkHandler()
    : pImpl(std::make_unique<Impl>())
    , host_("localhost")
    , port_(8080)
    , connected_(false)
    , bytesSent_(0)
    , bytesReceived_(0) {
}

NetworkHandler::NetworkHandler(const std::string& host, int port)
    : pImpl(std::make_unique<Impl>())
    , host_(host)
    , port_(port)
    , connected_(false)
    , bytesSent_(0)
    , bytesReceived_(0) {
}

NetworkHandler::~NetworkHandler() {
    stopAsyncReceive();
    disconnect();
}

NetworkHandler::NetworkHandler(NetworkHandler&& other) noexcept
    : pImpl(std::move(other.pImpl))
    , host_(std::move(other.host_))
    , port_(other.port_)
    , connected_(other.connected_)
    , lastError_(std::move(other.lastError_))
    , bytesSent_(other.bytesSent_)
    , bytesReceived_(other.bytesReceived_)
    , dataCallback_(std::move(other.dataCallback_)) {
    other.connected_ = false;
}

NetworkHandler& NetworkHandler::operator=(NetworkHandler&& other) noexcept {
    if (this != &other) {
        stopAsyncReceive();
        disconnect();

        pImpl = std::move(other.pImpl);
        host_ = std::move(other.host_);
        port_ = other.port_;
        connected_ = other.connected_;
        lastError_ = std::move(other.lastError_);
        bytesSent_ = other.bytesSent_;
        bytesReceived_ = other.bytesReceived_;
        dataCallback_ = std::move(other.dataCallback_);

        other.connected_ = false;
    }
    return *this;
}

bool NetworkHandler::connect() {
    if (connected_) {
        lastError_ = "Already connected";
        return false;
    }

    // 模拟连接逻辑
    std::cout << "Connecting to " << host_ << ":" << port_ << "..." << std::endl;

    // 这里可以添加实际的 socket 连接逻辑
    connected_ = true;
    lastError_.clear();

    std::cout << "Connected successfully" << std::endl;
    return true;
}

void NetworkHandler::disconnect() {
    if (!connected_) {
        return;
    }

    std::cout << "Disconnecting..." << std::endl;
    connected_ = false;
    lastError_.clear();
}

bool NetworkHandler::isConnected() const {
    return connected_;
}

bool NetworkHandler::send(const std::string& data) {
    if (!connected_) {
        lastError_ = "Not connected";
        return false;
    }

    // 模拟发送逻辑
    std::cout << "Sending " << data.size() << " bytes" << std::endl;
    bytesSent_ += data.size();

    return true;
}

std::string NetworkHandler::receive() {
    if (!connected_) {
        lastError_ = "Not connected";
        return "";
    }

    // 模拟接收逻辑
    std::string data = "Mock received data";
    bytesReceived_ += data.size();

    return data;
}

void NetworkHandler::setDataCallback(DataCallback callback) {
    dataCallback_ = std::move(callback);
}

void NetworkHandler::startAsyncReceive() {
    if (!pImpl || pImpl->asyncRunning) {
        return;
    }

    pImpl->asyncRunning = true;
    pImpl->asyncThread = std::thread([this]() {
        while (pImpl->asyncRunning && connected_) {
            std::string data = receive();
            if (!data.empty() && dataCallback_) {
                dataCallback_(data);
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    });
}

void NetworkHandler::stopAsyncReceive() {
    if (!pImpl) {
        return;
    }

    pImpl->asyncRunning = false;
    if (pImpl->asyncThread.joinable()) {
        pImpl->asyncThread.join();
    }
}

void NetworkHandler::setHost(const std::string& host) {
    host_ = host;
}

void NetworkHandler::setPort(int port) {
    port_ = port;
}

std::string NetworkHandler::getHost() const {
    return host_;
}

int NetworkHandler::getPort() const {
    return port_;
}

std::string NetworkHandler::getLastError() const {
    return lastError_;
}

size_t NetworkHandler::getBytesSent() const {
    return bytesSent_;
}

size_t NetworkHandler::getBytesReceived() const {
    return bytesReceived_;
}

} // namespace network
