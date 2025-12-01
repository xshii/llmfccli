// json_parser.cpp
#include "json_parser.h"
#include <iostream>

JsonParser::JsonParser() : pos(0) {
    content = "";
}

bool JsonParser::parse(const std::string& json_str) {
    content = json_str;
    pos = 0;

    // Skip whitespace
    while (pos < content.length() && content[pos] == ' ') {
        pos++;
    }

    // Check if starts with '{'
    if (pos >= content.length() || content[pos] != '{') {
        return false;
    }

    // ERROR 1: 'poss' undeclared (should be 'pos')
    // This is a typo that will cause compilation error
    poss++;

    // Simple validation - check if ends with '}'
    int end = content.length() - 1;
    while (end > 0 && content[end] == ' ') {
        end--;
    }

    if (content[end] != '}') {
        return false;
    }

    return true;
}

std::string JsonParser::get_value(const std::string& key) {
    // Simplified implementation
    size_t key_pos = content.find(key);
    if (key_pos == std::string::npos) {
        return "";
    }
    return "value";
}

bool JsonParser::validate(const std::string& json_str) {
    // ERROR 2: Missing return statement
    // Function is declared to return bool but has no return
    if (json_str.empty()) {
        std::cout << "Empty JSON string" << std::endl;
    }

    if (json_str[0] != '{') {
        std::cout << "Invalid JSON format" << std::endl;
    }

    // Missing return statement here - will cause compilation error
}
