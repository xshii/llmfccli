# Source library
add_library(sample_cpp_lib
    parser/json_parser.cpp
    network/network_handler.cpp
    http/http_module.cpp
)

target_include_directories(sample_cpp_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Main executable
add_executable(sample_cpp_app
    main.cpp
)

target_link_libraries(sample_cpp_app PRIVATE sample_cpp_lib)
