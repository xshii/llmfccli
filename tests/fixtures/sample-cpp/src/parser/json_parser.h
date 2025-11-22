#ifndef JSON_PARSER_H
#define JSON_PARSER_H

#include <string>
#include <map>
#include <variant>

using JsonValue = std::variant<std::string, int, double, bool>;

class JsonParser {
public:
    JsonParser();
    ~JsonParser();
    
    // Parse JSON string and return map
    std::map<std::string, JsonValue> parse(const std::string& json);
    
    // Validate JSON format
    bool validate(const std::string& json);
    
private:
    void skipWhitespace(const std::string& str, size_t& pos);
    std::string parseString(const std::string& str, size_t& pos);
    JsonValue parseValue(const std::string& str, size_t& pos);
};

#endif // JSON_PARSER_H
