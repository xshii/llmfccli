cmake_minimum_required(VERSION 3.10)
project(SampleCpp)

set(CMAKE_CXX_STANDARD 17)

# Source files
add_executable(sample_app
    src/main.cpp
    src/network_handler.cpp
)

# Include directories
target_include_directories(sample_app PRIVATE src)
