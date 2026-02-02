#pragma once

#include <string>
#include <functional>
#include <memory>

namespace network {

/**
 * NetworkHandler - 处理网络连接和数据传输
 *
 * 这是一个用于测试的示例类，包含一些故意的编译错误
 * 用于测试 Agent 的错误修复能力
 */
class NetworkHandler {
public:
    using DataCallback = std::function<void(const std::string&)>;

    NetworkHandler();
    explicit NetworkHandler(const std::string& host, int port = 8080);
    ~NetworkHandler();

    // 禁止拷贝
    NetworkHandler(const NetworkHandler&) = delete;
    NetworkHandler& operator=(const NetworkHandler&) = delete;

    // 允许移动
    NetworkHandler(NetworkHandler&&) noexcept;
    NetworkHandler& operator=(NetworkHandler&&) noexcept;

    // 连接管理
    bool connect();
    void disconnect();
    bool isConnected() const;

    // 数据传输
    bool send(const std::string& data);
    std::string receive();

    // 异步操作
    void setDataCallback(DataCallback callback);
    void startAsyncReceive();
    void stopAsyncReceive();

    // 配置
    void setHost(const std::string& host);
    void setPort(int port);
    std::string getHost() const;
    int getPort() const;

    // 状态
    std::string getLastError() const;
    size_t getBytesSent() const;
    size_t getBytesReceived() const;

private:
    struct Impl;
    std::unique_ptr<Impl> pImpl;

    std::string host_;
    int port_;
    bool connected_;
    std::string lastError_;
    size_t bytesSent_;
    size_t bytesReceived_;
    DataCallback dataCallback_;
};

} // namespace network
