cmake_minimum_required(VERSION 3.14)
project(calculator)

set(CMAKE_CXX_STANDARD 17)

include_directories(include)

add_library(calculator src/calculator.cpp)

# Google Test
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
FetchContent_MakeAvailable(googletest)

enable_testing()
add_executable(test_calculator tests/test_calculator.cpp)
target_link_libraries(test_calculator calculator GTest::gtest_main)
add_test(NAME test_calculator COMMAND test_calculator)
