#include <gtest/gtest.h>
#include "string_utils.h"

TEST(StringUtilsTest, Trim) {
    EXPECT_EQ(utils::trim("  hello  "), "hello");
    EXPECT_EQ(utils::trim("no spaces"), "no spaces");
    EXPECT_EQ(utils::trim("   "), "");
}

TEST(StringUtilsTest, Split) {
    auto parts = utils::split("a,b,c", ',');
    ASSERT_EQ(parts.size(), 3);
    EXPECT_EQ(parts[0], "a");
    EXPECT_EQ(parts[1], "b");
    EXPECT_EQ(parts[2], "c");
}

TEST(StringUtilsTest, Join) {
    std::vector<std::string> parts = {"a", "b", "c"};
    EXPECT_EQ(utils::join(parts, ","), "a,b,c");
    EXPECT_EQ(utils::join(parts, " - "), "a - b - c");
}

TEST(StringUtilsTest, ToUpper) {
    EXPECT_EQ(utils::to_upper("hello"), "HELLO");
    EXPECT_EQ(utils::to_upper("Hello World"), "HELLO WORLD");
}

TEST(StringUtilsTest, ToLower) {
    EXPECT_EQ(utils::to_lower("HELLO"), "hello");
    EXPECT_EQ(utils::to_lower("Hello World"), "hello world");
}
