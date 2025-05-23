#ifndef SUNPOSITION_H
#define SUNPOSITION_H

#include "sunpos.h"
#include <Eigen/Dense>
#include <chrono>

class SunPosition {
public:
    static Eigen::Vector3d getSunDirection(const std::chrono::system_clock::time_point& utc,
                                           double latitude, double longitude);
};

#endif // SUNPOSITION_H