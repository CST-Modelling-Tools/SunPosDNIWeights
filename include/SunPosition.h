#ifndef SUN_POSITION_H
#define SUN_POSITION_H

#include "sunpos.h"        // cTime, cLocation, cSunCoordinates
#include <Eigen/Dense>

class SunPosition {
public:
    static Eigen::Vector3d getSunDirection(const cTime& utc,
                                           double latitude,
                                           double longitude);
};

#endif // SUN_POSITION_H