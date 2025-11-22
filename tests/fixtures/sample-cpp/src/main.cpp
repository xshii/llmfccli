#include <iostream>
#include "parser/json_parser.h"
#include "network/network_handler.h"

int main(int argc, char** argv) {
    std::cout << "Sample C++ Project" << std::endl;
    
    // Test JSON parser
    JsonParser parser;
    std::string json = R"({"name": "test", "value": 42})";
    auto result = parser.parse(json);
    
    // Test network handler
    NetworkHandler handler;
    handler.connect("localhost", 8080);
    
    return 0;
}
