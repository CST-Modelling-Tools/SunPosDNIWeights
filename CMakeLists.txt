cmake_minimum_required(VERSION 3.15)
project(PolyharmonicEnergy LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Let the user optionally override the Eigen path
set(EIGEN3_INCLUDE_DIR "C:/eigen" CACHE PATH "Path to Eigen include directory")

# Add external dependencies first
add_subdirectory(external/sunpos)

# Add internal libraries and applications
add_subdirectory(src)
add_subdirectory(apps/AnnualEnergy)
add_subdirectory(tools/GenerateSamplingDirectionsAndWeights)