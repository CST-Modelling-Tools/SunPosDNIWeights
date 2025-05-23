#include "SunPosition.h"
#include <ctime>
#include <Eigen/Dense>

Eigen::Vector3d SunPosition::getSunDirection(const std::chrono::system_clock::time_point& utc,
                                             double latitude, double longitude) {
    std::time_t tt = std::chrono::system_clock::to_time_t(utc);
    std::tm* gmt = std::gmtime(&tt);

    cTime time = {
        gmt->tm_year + 1900,
        gmt->tm_mon + 1,
        gmt->tm_mday,
        static_cast<double>(gmt->tm_hour),
        static_cast<double>(gmt->tm_min),
        static_cast<double>(gmt->tm_sec)
    };

    cLocation loc = { longitude, latitude };
    cSunCoordinates coord;
    sunpos(time, loc, &coord);

    // Angles are already in radians
    double zenith = coord.dZenithAngle;
    double azimuth = coord.dAzimuth;

    // ENZ vector (East-North-Zenith frame)
    double x = std::sin(azimuth) * std::sin(zenith); // East
    double y = std::cos(azimuth) * std::sin(zenith); // North
    double z = std::cos(zenith);                     // Zenith

    return Eigen::Vector3d(x, y, z).normalized();
}