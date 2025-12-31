cmake_minimum_required(VERSION 3.14)
project(validator)

set(CMAKE_CXX_STANDARD 17)

include_directories(include)

add_library(validator src/validator.cpp)

# Google Test
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
FetchContent_MakeAvailable(googletest)

enable_testing()
add_executable(test_validator tests/test_validator.cpp)
target_link_libraries(test_validator validator GTest::gtest_main)
add_test(NAME test_validator COMMAND test_validator)
