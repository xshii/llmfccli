#include "http_module.h"
#include <sstream>

HttpClient::HttpClient() : port_(80) {
}

HttpClient::~HttpClient() {
}

bool HttpClient::connect(const std::string& host, int port) {
    host_ = host;
    port_ = port;
    return networkHandler_.connect(host, port);
}

HttpResponse HttpClient::sendRequest(const HttpRequest& request) {
    std::string requestStr = buildRequestString(request);
    
    if (!networkHandler_.send(requestStr)) {
        return HttpResponse{500, {}, "Failed to send request"};
    }
    
    std::string responseStr = networkHandler_.receive();
    return parseResponse(responseStr);
}

HttpResponse HttpClient::get(const std::string& path) {
    HttpRequest request;
    request.method = HttpMethod::GET;
    request.path = path;
    request.headers["Host"] = host_;
    return sendRequest(request);
}

HttpResponse HttpClient::post(const std::string& path, const std::string& body) {
    HttpRequest request;
    request.method = HttpMethod::POST;
    request.path = path;
    request.headers["Host"] = host_;
    request.headers["Content-Length"] = std::to_string(body.size());
    request.body = body;
    return sendRequest(request);
}

std::string HttpClient::buildRequestString(const HttpRequest& request) {
    std::ostringstream oss;
    
    // Request line
    switch (request.method) {
        case HttpMethod::GET:    oss << "GET "; break;
        case HttpMethod::POST:   oss << "POST "; break;
        case HttpMethod::PUT:    oss << "PUT "; break;
        case HttpMethod::DELETE: oss << "DELETE "; break;
    }
    oss << request.path << " HTTP/1.1\r\n";
    
    // Headers
    for (const auto& [key, value] : request.headers) {
        oss << key << ": " << value << "\r\n";
    }
    oss << "\r\n";
    
    // Body
    if (!request.body.empty()) {
        oss << request.body;
    }
    
    return oss.str();
}

HttpResponse HttpClient::parseResponse(const std::string& responseStr) {
    HttpResponse response;
    
    std::istringstream iss(responseStr);
    std::string line;
    
    // Parse status line
    if (std::getline(iss, line)) {
        std::istringstream statusLine(line);
        std::string httpVersion;
        statusLine >> httpVersion >> response.statusCode;
    }
    
    // Parse headers
    while (std::getline(iss, line) && line != "\r") {
        size_t colonPos = line.find(':');
        if (colonPos != std::string::npos) {
            std::string key = line.substr(0, colonPos);
            std::string value = line.substr(colonPos + 2); // Skip ": "
            if (!value.empty() && value.back() == '\r') {
                value.pop_back();
            }
            response.headers[key] = value;
        }
    }
    
    // Parse body
    std::ostringstream bodyStream;
    while (std::getline(iss, line)) {
        bodyStream << line;
    }
    response.body = bodyStream.str();
    
    return response;
}
