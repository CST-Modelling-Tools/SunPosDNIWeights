#ifndef DIRECTION_UTILS_H
#define DIRECTION_UTILS_H

#include <Eigen/Dense>
#include <numbers>

namespace DirectionUtils {

// Converts azimuth (from North toward East) and elevation (above horizon) [degrees]
// to ENZ unit vector {x, y, z}
inline Eigen::Vector3d AzElToUnitVector(double azimuth_deg, double elevation_deg) {
    double az_rad = azimuth_deg * std::numbers::pi / 180.0;
    double el_rad = elevation_deg * std::numbers::pi / 180.0;

    double x = std::sin(az_rad) * std::cos(el_rad); // East
    double y = std::cos(az_rad) * std::cos(el_rad); // North
    double z = std::sin(el_rad);                    // Zenith

    return Eigen::Vector3d(x, y, z);
}

} // namespace DirectionUtils

#endif // DIRECTION_UTILS_H