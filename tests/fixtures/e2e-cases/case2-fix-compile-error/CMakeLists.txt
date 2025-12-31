cmake_minimum_required(VERSION 3.14)
project(string_utils)

set(CMAKE_CXX_STANDARD 17)

include_directories(include)

add_library(string_utils src/string_utils.cpp)

# Google Test
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
FetchContent_MakeAvailable(googletest)

enable_testing()
add_executable(test_string_utils tests/test_string_utils.cpp)
target_link_libraries(test_string_utils string_utils GTest::gtest_main)
add_test(NAME test_string_utils COMMAND test_string_utils)
