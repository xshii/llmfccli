#include "json_parser.h"
#include <stdexcept>
#include <cctype>

JsonParser::JsonParser() {
    // Constructor
}

JsonParser::~JsonParser() {
    // Destructor
}

std::map<std::string, JsonValue> JsonParser::parse(const std::string& json) {
    std::map<std::string, JsonValue> result;
    size_t pos = 0;
    
    skipWhitespace(json, pos);
    
    // Error 1: Missing check for opening brace
    if (json[pos] != '{') {
        throw std::runtime_error("Expected '{' at start");
    }
    pos++;
    
    while (pos < json.size()) {
        skipWhitespace(json, pos);
        
        if (json[pos] == '}') {
            break;
        }
        
        // Parse key
        std::string key = parseString(json, pos);
        skipWhitespace(json, pos);
        
        // Error 2: Typo - should be json[pos] != ':'
        if (json[poss] != ':') {  // Compilation error: 'poss' undeclared
            throw std::runtime_error("Expected ':' after key");
        }
        pos++;
        
        skipWhitespace(json, pos);
        
        // Parse value
        JsonValue value = parseValue(json, pos);
        result[key] = value;
        
        skipWhitespace(json, pos);
        
        if (json[pos] == ',') {
            pos++;
        }
    }
    
    return result;
}

bool JsonParser::validate(const std::string& json) {
    // Error 3: Missing return statement (warning that will become error with -Werror)
    try {
        parse(json);
    } catch (...) {
        return false;
    }
    // Missing: return true;
}

void JsonParser::skipWhitespace(const std::string& str, size_t& pos) {
    while (pos < str.size() && std::isspace(str[pos])) {
        pos++;
    }
}

std::string JsonParser::parseString(const std::string& str, size_t& pos) {
    if (str[pos] != '"') {
        throw std::runtime_error("Expected '\"' at start of string");
    }
    pos++;
    
    std::string result;
    while (pos < str.size() && str[pos] != '"') {
        result += str[pos];
        pos++;
    }
    
    if (pos >= str.size()) {
        throw std::runtime_error("Unterminated string");
    }
    
    pos++; // Skip closing quote
    return result;
}

JsonValue JsonParser::parseValue(const std::string& str, size_t& pos) {
    skipWhitespace(str, pos);
    
    if (str[pos] == '"') {
        return parseString(str, pos);
    } else if (std::isdigit(str[pos]) || str[pos] == '-') {
        // Parse number (simplified)
        size_t start = pos;
        while (pos < str.size() && (std::isdigit(str[pos]) || str[pos] == '.')) {
            pos++;
        }
        std::string numStr = str.substr(start, pos - start);
        if (numStr.find('.') != std::string::npos) {
            return std::stod(numStr);
        } else {
            return std::stoi(numStr);
        }
    } else if (str.substr(pos, 4) == "true") {
        pos += 4;
        return true;
    } else if (str.substr(pos, 5) == "false") {
        pos += 5;
        return false;
    }
    
    throw std::runtime_error("Unexpected value");
}
