cmake_minimum_required(VERSION 3.15)
project(SampleCppProject VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable testing
enable_testing()

# Add subdirectories
add_subdirectory(src)
add_subdirectory(tests)

# Option to build tests
option(BUILD_TESTS "Build the tests" ON)
