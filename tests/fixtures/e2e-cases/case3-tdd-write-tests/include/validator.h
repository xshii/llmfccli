#pragma once

#include <string>
#include <regex>

class EmailValidator {
public:
    // 验证邮箱格式是否正确
    bool isValid(const std::string& email) const;

    // 获取邮箱的用户名部分 (@ 之前)
    std::string getUsername(const std::string& email) const;

    // 获取邮箱的域名部分 (@ 之后)
    std::string getDomain(const std::string& email) const;

    // 检查是否为企业邮箱 (非 gmail, hotmail, yahoo 等)
    bool isCorporate(const std::string& email) const;
};
