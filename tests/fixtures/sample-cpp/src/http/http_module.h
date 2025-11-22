#ifndef HTTP_MODULE_H
#define HTTP_MODULE_H

#include <string>
#include <map>
#include "../network/network_handler.h"

enum class HttpMethod {
    GET,
    POST,
    PUT,
    DELETE
};

struct HttpRequest {
    HttpMethod method;
    std::string path;
    std::map<std::string, std::string> headers;
    std::string body;
};

struct HttpResponse {
    int statusCode;
    std::map<std::string, std::string> headers;
    std::string body;
};

class HttpClient {
public:
    HttpClient();
    ~HttpClient();
    
    // Connect to HTTP server
    bool connect(const std::string& host, int port);
    
    // Send HTTP request
    HttpResponse sendRequest(const HttpRequest& request);
    
    // GET request helper
    HttpResponse get(const std::string& path);
    
    // POST request helper
    HttpResponse post(const std::string& path, const std::string& body);
    
private:
    NetworkHandler networkHandler_;
    std::string host_;
    int port_;
    
    std::string buildRequestString(const HttpRequest& request);
    HttpResponse parseResponse(const std::string& responseStr);
};

#endif // HTTP_MODULE_H
