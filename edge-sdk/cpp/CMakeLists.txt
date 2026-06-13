cmake_minimum_required(VERSION 3.16)
project(uav_edge_sdk
    VERSION 1.0.0
    DESCRIPTION "UAV Edge Computing SDK - 无人机边缘计算 C++ SDK"
    LANGUAGES CXX
)

# 要求 C++17 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 导出编译选项
set(UAV_EDGE_SDK_COMPILE_OPTIONS
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /utf-8>
    $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall -Wextra -Wpedantic>
)

# ---- 头文件路径 ----
target_include_directories(uav_edge_sdk INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# ---- 可选依赖 ----
# ONNX Runtime（模型推理）
find_package(ONNXRuntime QUIET)
if(ONNXRuntime_FOUND)
    message(STATUS "ONNXRuntime found, enabling model inference backend")
    target_link_libraries(uav_edge_sdk INTERFACE onnxruntime)
    target_compile_definitions(uav_edge_sdk INTERFACE UAV_EDGE_HAS_ONNXRUNTIME)
else()
    message(STATUS "ONNXRuntime not found, model inference backend will be stubbed")
endif()

# nlohmann/json（配置管理）
find_package(nlohmann_json QUIET)
if(nlohmann_json_FOUND)
    message(STATUS "nlohmann_json found, enabling JSON config support")
    target_link_libraries(uav_edge_sdk INTERFACE nlohmann_json::nlohmann_json)
    target_compile_definitions(uav_edge_sdk INTERFACE UAV_EDGE_HAS_JSON)
else()
    message(STATUS "nlohmann_json not found, JSON config support will be limited")
endif()

# ---- 示例库（编译所有源文件） ----
file(GLOB_RECURSE UAV_EDGE_SOURCES src/*.cpp)

add_library(uav_edge_sdk_impl STATIC ${UAV_EDGE_SOURCES})
target_include_directories(uav_edge_sdk_impl PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_compile_options(uav_edge_sdk_impl PRIVATE ${UAV_EDGE_SDK_COMPILE_OPTIONS})

if(ONNXRuntime_FOUND)
    target_link_libraries(uav_edge_sdk_impl PUBLIC onnxruntime)
    target_compile_definitions(uav_edge_sdk_impl PUBLIC UAV_EDGE_HAS_ONNXRUNTIME)
endif()

if(nlohmann_json_FOUND)
    target_link_libraries(uav_edge_sdk_impl PUBLIC nlohmann_json::nlohmann_json)
    target_compile_definitions(uav_edge_sdk_impl PUBLIC UAV_EDGE_HAS_JSON)
endif()

# ---- 测试 ----
option(UAV_EDGE_BUILD_TESTS "Build unit tests" OFF)
if(UAV_EDGE_BUILD_TESTS)
    enable_testing()
    find_package(GTest QUIET)
    if(GTest_FOUND)
        add_subdirectory(tests)
    else()
        message(WARNING "GTest not found, skipping tests")
    endif()
endif()

# ---- 安装规则 ----
install(DIRECTORY include/uav_edge DESTINATION include)
install(TARGETS uav_edge_sdk_impl
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)
