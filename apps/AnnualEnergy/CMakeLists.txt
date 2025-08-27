add_executable(AnnualEnergy main.cpp)

# Link to the core library
target_link_libraries(AnnualEnergy PRIVATE polyharmonic_core)

# Ensure Eigen is available to this target if not already inherited
target_include_directories(AnnualEnergy PRIVATE ${Eigen3_INCLUDE_DIRS})