// main.cpp
#include <iostream>
#include "network_handler.h"

int main() {
    std::cout << "Hello World" << std::endl;

    NetworkHandler handler;
    handler.connect("localhost");
    handler.disconnect();

    return 0;
}
