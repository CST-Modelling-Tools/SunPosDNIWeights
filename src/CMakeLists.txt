add_library(polyharmonic_core
    Interpolator.cpp
    DNISeries.cpp
    SunPosition.cpp
    AnnualEnergyCalculator.cpp
)

target_include_directories(polyharmonic_core
    PUBLIC
        ${CMAKE_SOURCE_DIR}/include
        ${EIGEN3_INCLUDE_DIR}       # 💡 Your local Eigen headers
)

target_link_libraries(polyharmonic_core
    PUBLIC sunpos                 # 💡 External sun position module
)
