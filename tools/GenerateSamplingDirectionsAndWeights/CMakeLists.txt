cmake_minimum_required(VERSION 3.15)

project(GenerateSamplingDirectionsAndWeights LANGUAGES CXX)

add_executable(GenerateSamplingDirectionsAndWeights main.cpp)

target_link_libraries(GenerateSamplingDirectionsAndWeights
    PRIVATE
        polyharmonic_core
)

# Prevent Windows macro conflict
target_compile_definitions(GenerateSamplingDirectionsAndWeights PRIVATE NOMINMAX)

# Add Eigen and local headers
target_include_directories(GenerateSamplingDirectionsAndWeights
    PRIVATE
        ${CMAKE_SOURCE_DIR}/include
        ${Eigen3_INCLUDE_DIRS}
)