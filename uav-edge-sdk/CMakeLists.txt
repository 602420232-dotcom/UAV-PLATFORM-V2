cmake_minimum_required(VERSION 3.10)
project(uav_edge_sdk)

# Set C++ standard to C++17 (required for modern C++ features)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")

# Compiler warnings and options
if(MSVC)
    # MSVC: Enable high warning level, treat warnings as errors, and UTF-8 encoding
    add_compile_options(/W4 /WX /utf-8)
    add_compile_definitions(_UNICODE UNICODE)
else()
    # GCC/Clang: Enable all warnings and treat warnings as errors
    add_compile_options(-Wall -Wextra -Werror)
endif()

# Find Python
find_package(Python COMPONENTS Interpreter Development REQUIRED)

# Find pybind11
# Option 1: Use CMake's Findpybind11 (CMake 3.15+)
find_package(pybind11 CONFIG QUIET)

if(NOT pybind11_FOUND)
    # Option 2: Fetch pybind11 from GitHub
    include(FetchContent)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG v2.11.1
    )
    FetchContent_MakeAvailable(pybind11)
endif()

message(STATUS "pybind11 found: ${pybind11_FOUND}")

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Source files
set(SOURCES
    src/path_planner.cpp
    src/risk_assessor.cpp
    src/flight_controller.cpp
    src/dwa_planner.cpp
    src/trajectory_corrector.cpp
    src/path_smoother.cpp
    src/offline_cache.cpp
    src/bindings.cpp
)

# Create Python module
pybind11_add_module(edge_sdk_cpp ${SOURCES})

# Set output directory
set_target_properties(edge_sdk_cpp PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/python
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/python
)

# Install target
install(TARGETS edge_sdk_cpp
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}/python
)

# Print configuration summary
message(STATUS "")
message(STATUS "==================================")
message(STATUS "  UAV Edge SDK Configuration")
message(STATUS "==================================")
message(STATUS "  Python Include: ${Python_INCLUDE_DIRS}")
message(STATUS "  Python Version: ${Python_VERSION}")
message(STATUS "  CMake: ${CMAKE_VERSION}")
message(STATUS "  C++ Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Install Path: ${CMAKE_CURRENT_SOURCE_DIR}/python")
message(STATUS "==================================")
message(STATUS "")
