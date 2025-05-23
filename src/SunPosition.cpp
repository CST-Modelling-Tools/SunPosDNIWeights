#include "SunPosition.h"

Eigen::Vector3d SunPosition::getSunDirection(const cTime& utc,
                                             double latitude,
                                             double longitude) {
    cLocation loc = { longitude, latitude };
    cSunCoordinates coord;

    sunpos(utc, loc, &coord);

    double zenith = coord.dZenithAngle;  // already in radians
    double azimuth = coord.dAzimuth;     // already in radians

    double x = std::sin(azimuth) * std::sin(zenith); // East
    double y = std::cos(azimuth) * std::sin(zenith); // North
    double z = std::cos(zenith);                     // Zenith

    return Eigen::Vector3d(x, y, z).normalized();
}