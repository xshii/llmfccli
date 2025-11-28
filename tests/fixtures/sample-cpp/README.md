# Sample C++ Project (Test Fixture)

这是一个简单的 C++ 测试项目，用于测试 Claude-Qwen 的功能。

## 结构

```
sample-cpp/
├── src/
│   ├── main.cpp             # 主程序
│   ├── network_handler.cpp  # NetworkHandler 实现
│   └── network_handler.h    # NetworkHandler 头文件
├── CMakeLists.txt           # CMake 配置
└── README.md                # 本文件
```

## 已知问题

- `network_handler.cpp:connect()` 缺少超时重试机制

## 构建

```bash
mkdir build && cd build
cmake ..
make
```
