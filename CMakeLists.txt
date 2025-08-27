cmake_minimum_required(VERSION 3.15)
project(PolyharmonicEnergy LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ------------------------------------------------------------------------------------
# Cross-platform Eigen detection
# ------------------------------------------------------------------------------------
# Try to find Eigen3 via system config or user-provided path
find_package(Eigen3 QUIET NO_MODULE)

if (NOT Eigen3_FOUND)
    message(STATUS "Eigen3 not found via find_package. Falling back to manual path.")

    # Let the user override the Eigen path manually (Windows or custom installs)
    set(EIGEN3_INCLUDE_DIR "C:/eigen" CACHE PATH "Path to Eigen include directory")
    if (EXISTS "${EIGEN3_INCLUDE_DIR}/Eigen")
        set(Eigen3_INCLUDE_DIRS ${EIGEN3_INCLUDE_DIR})
    else()
        message(FATAL_ERROR "Could not find Eigen3. Please install it or set EIGEN3_INCLUDE_DIR.")
    endif()
else()
    message(STATUS "Eigen3 found via find_package.")
    set(Eigen3_INCLUDE_DIRS ${EIGEN3_INCLUDE_DIRS})
endif()

# Make Eigen3 include directory available to all targets
include_directories(SYSTEM ${Eigen3_INCLUDE_DIRS})

# ------------------------------------------------------------------------------------
# Add external and internal components
# ------------------------------------------------------------------------------------
add_subdirectory(external/sunpos)
add_subdirectory(src)
add_subdirectory(apps/AnnualEnergy)
add_subdirectory(tools/GenerateSamplingDirectionsAndWeights)