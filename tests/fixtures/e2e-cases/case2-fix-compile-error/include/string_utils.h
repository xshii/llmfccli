#pragma once

#include <string>
#include <vector>

namespace utils {

std::string trim(const std::string& str);
std::vector<std::string> split(const std::string& str, char delimiter);
std::string join(const std::vector<std::string>& parts, const std::string& separator);
std::string to_upper(const std::string& str);
std::string to_lower(const std::string& str);

}  // namespace utils
