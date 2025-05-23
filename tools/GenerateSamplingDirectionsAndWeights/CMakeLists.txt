cmake_minimum_required(VERSION 3.15)

project(GenerateSamplingDirectionsAndWeights LANGUAGES CXX)

add_executable(GenerateSamplingDirectionsAndWeights main.cpp)

target_link_libraries(GenerateSamplingDirectionsAndWeights
    PRIVATE
        polyharmonic_core
)

target_compile_definitions(GenerateSamplingDirectionsAndWeights PRIVATE NOMINMAX)

# Optional: add path to Eigen if needed (if not already handled globally)
target_include_directories(GenerateSamplingDirectionsAndWeights
    PRIVATE
        ${CMAKE_SOURCE_DIR}/include
        ${EIGEN3_INCLUDE_DIR}
)