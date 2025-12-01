// json_parser.h
#ifndef JSON_PARSER_H
#define JSON_PARSER_H

#include <string>

class JsonParser {
public:
    JsonParser();
    bool parse(const std::string& json_str);
    bool validate(const std::string& json_str);
    std::string get_value(const std::string& key);

private:
    std::string content;
    int pos;
};

#endif // JSON_PARSER_H
