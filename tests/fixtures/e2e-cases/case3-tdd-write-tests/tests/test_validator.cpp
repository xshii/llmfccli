#include <gtest/gtest.h>
#include "validator.h"

class EmailValidatorTest : public ::testing::Test {
protected:
    EmailValidator validator;
};

// isValid 测试
TEST_F(EmailValidatorTest, ValidEmails) {
    EXPECT_TRUE(validator.isValid("user@example.com"));
    EXPECT_TRUE(validator.isValid("user.name@example.com"));
    EXPECT_TRUE(validator.isValid("user+tag@example.co.uk"));
    EXPECT_TRUE(validator.isValid("user123@sub.example.com"));
}

TEST_F(EmailValidatorTest, InvalidEmails) {
    EXPECT_FALSE(validator.isValid(""));
    EXPECT_FALSE(validator.isValid("invalid"));
    EXPECT_FALSE(validator.isValid("@example.com"));
    EXPECT_FALSE(validator.isValid("user@"));
    EXPECT_FALSE(validator.isValid("user@@example.com"));
    EXPECT_FALSE(validator.isValid("user@.com"));
}

// getUsername 测试
TEST_F(EmailValidatorTest, GetUsername) {
    EXPECT_EQ(validator.getUsername("user@example.com"), "user");
    EXPECT_EQ(validator.getUsername("john.doe@company.com"), "john.doe");
    EXPECT_EQ(validator.getUsername("test+filter@gmail.com"), "test+filter");
}

TEST_F(EmailValidatorTest, GetUsernameInvalid) {
    EXPECT_EQ(validator.getUsername("invalid"), "");
    EXPECT_EQ(validator.getUsername(""), "");
}

// getDomain 测试
TEST_F(EmailValidatorTest, GetDomain) {
    EXPECT_EQ(validator.getDomain("user@example.com"), "example.com");
    EXPECT_EQ(validator.getDomain("user@sub.example.co.uk"), "sub.example.co.uk");
}

TEST_F(EmailValidatorTest, GetDomainInvalid) {
    EXPECT_EQ(validator.getDomain("invalid"), "");
    EXPECT_EQ(validator.getDomain(""), "");
}

// isCorporate 测试
TEST_F(EmailValidatorTest, CorporateEmails) {
    EXPECT_TRUE(validator.isCorporate("user@company.com"));
    EXPECT_TRUE(validator.isCorporate("admin@startup.io"));
    EXPECT_TRUE(validator.isCorporate("info@enterprise.org"));
}

TEST_F(EmailValidatorTest, PersonalEmails) {
    EXPECT_FALSE(validator.isCorporate("user@gmail.com"));
    EXPECT_FALSE(validator.isCorporate("user@hotmail.com"));
    EXPECT_FALSE(validator.isCorporate("user@yahoo.com"));
    EXPECT_FALSE(validator.isCorporate("user@outlook.com"));
    EXPECT_FALSE(validator.isCorporate("user@qq.com"));
    EXPECT_FALSE(validator.isCorporate("user@163.com"));
}
