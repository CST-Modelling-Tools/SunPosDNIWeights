cmake_minimum_required(VERSION 3.15)
project(PolyharmonicEnergy LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ------------------------------------------------------------------------------------
# Eigen3 detection
# ------------------------------------------------------------------------------------
find_package(Eigen3 3.3 QUIET NO_MODULE)

if (Eigen3_FOUND)
    message(STATUS "Eigen3 found via find_package at: ${EIGEN_INCLUDE_DIR}")
else()
    message(STATUS "Eigen3 not found via find_package. Using manual path.")

    # Try to get path from environment variable first
    if (DEFINED ENV{EIGEN_INCLUDE_DIR})
        set(EIGEN_INCLUDE_DIR "$ENV{EIGEN_INCLUDE_DIR}" CACHE PATH "Path to Eigen include directory")
        message(STATUS "Using EIGEN_INCLUDE_DIR from environment variable: ${EIGEN_INCLUDE_DIR}")
    else()
        # If environment variable not set, allow CMake configuration to override
        set(EIGEN_INCLUDE_DIR "" CACHE PATH "Path to Eigen include directory")
    endif()

    if (NOT EIGEN_INCLUDE_DIR)
        message(FATAL_ERROR "Could not find Eigen3. Please either:\n"
                            "  1. Set the EIGEN_INCLUDE_DIR environment variable, or\n"
                            "  2. Pass -DEIGEN_INCLUDE_DIR=/path/to/eigen to CMake, or\n"
                            "  3. Install Eigen where CMake can find it via find_package()")
    endif()

    if (EXISTS "${EIGEN_INCLUDE_DIR}/Eigen/Core")
        message(STATUS "Eigen manually located at: ${EIGEN_INCLUDE_DIR}")
    else()
        message(FATAL_ERROR "EIGEN_INCLUDE_DIR is set to '${EIGEN_INCLUDE_DIR}', but Eigen/Core was not found there.\n"
                            "Please verify the path points to the Eigen root directory.")
    endif()

    # Create an imported target for consistency
    add_library(Eigen3::Eigen INTERFACE IMPORTED)
    set_target_properties(Eigen3::Eigen PROPERTIES
        INTERFACE_INCLUDE_DIRECTORIES "${EIGEN_INCLUDE_DIR}"
    )
endif()

# ------------------------------------------------------------------------------------
# Silence Eigen's internal warnings (C++20+ enum conversions)
# ------------------------------------------------------------------------------------

# Treat Eigen includes as system headers — hides warnings from Eigen but keeps yours
if (TARGET Eigen3::Eigen)
    get_target_property(_eigen_inc Eigen3::Eigen INTERFACE_INCLUDE_DIRECTORIES)
    if (_eigen_inc)
        set_target_properties(Eigen3::Eigen PROPERTIES
            INTERFACE_SYSTEM_INCLUDE_DIRECTORIES "${_eigen_inc}"
        )
        message(STATUS "Eigen headers marked as SYSTEM to suppress internal warnings.")
    endif()
endif()

# Fallback: explicitly suppress enum conversion warnings on modern compilers
if (CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    add_compile_options(-Wno-deprecated-enum-enum-conversion)
elseif (MSVC)
    add_compile_options(/wd5054)
endif()

# ------------------------------------------------------------------------------------
# Add subdirectories
# ------------------------------------------------------------------------------------
add_subdirectory(external/sunpos)
add_subdirectory(src)
add_subdirectory(apps/AnnualEnergy)
add_subdirectory(tools/GenerateSamplingDirectionsAndWeights)