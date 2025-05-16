cmake_minimum_required(VERSION 3.15)
project(SunPositionDNIWeights)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include paths
include_directories(include)
include_directories(external/sunpos)

# Source files from src/ and external/sunpos/
file(GLOB SRC_FILES
    "src/*.cpp"
    "external/sunpos/sunpos.cpp"
)

# Executable target
add_executable(SunPositionDNIWeights
    main.cpp
    ${SRC_FILES}
)
