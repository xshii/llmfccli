#include "string_utils.h"
// 错误1: 缺少 #include <algorithm> 和 <sstream>

namespace utils {

std::string trim(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\n\r");
    size_t end = str.find_last_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    return str.substr(start, end - start + 1);
}

std::vector<std::string> split(const std::string& str, char delimiter) {
    std::vector<std::string> result;
    std::stringstream ss(str);  // 错误2: stringstream 未定义
    std::string item;
    while (std::getline(ss, item, delimiter)) {
        result.push_back(item);
    }
    return result;
}

std::string join(const std::vector<std::string>& parts, const std::string& separator) {
    std::string result;
    for (size_t i = 0; i < parts.size(); ++i) {
        if (i > 0) result += separator;
        result += parts[i];
    }
    // 错误3: 缺少 return 语句
}

std::string to_upper(const std::string& str) {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(), ::toupper);  // 错误4: transform 未定义
    return result;
}

std::string to_lower(const std::string& str) {
    std::string result = str
    std::transform(result.begin(), result.end(), result.begin(), ::tolower);  // 错误5: 上一行缺少分号
    return result;
}

}  // namespace utils
