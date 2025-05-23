#ifndef LOADER_H
#define LOADER_H

#include <vector>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <Eigen/Dense>
#include <numbers>

// Converts azimuth/elevation (in degrees) to ENZ unit vector
inline Eigen::Vector3d AzElToUnitVector(double azimuth_deg, double elevation_deg) {
    double az = azimuth_deg * std::numbers::pi / 180.0;
    double el = elevation_deg * std::numbers::pi / 180.0;

    double x = std::sin(az) * std::cos(el); // East
    double y = std::cos(az) * std::cos(el); // North
    double z = std::sin(el);                // Zenith

    return Eigen::Vector3d(x, y, z);
}

// Reads lines like: azimuth, elevation, efficiency
inline void loadAzElEfficiencies(
    const std::string& file,
    std::vector<Eigen::Vector3d>& directions,
    std::vector<double>& efficiencies)
{
    std::ifstream in(file);
    if (!in) throw std::runtime_error("Failed to open file: " + file);

    std::string line;
    while (std::getline(in, line)) {
        std::istringstream ss(line);
        double azimuth, elevation, eta;
        char comma;
        if (!(ss >> azimuth >> comma >> elevation >> comma >> eta)) {
            throw std::runtime_error("Malformed line: " + line);
        }
        directions.push_back(AzElToUnitVector(azimuth, elevation));
        efficiencies.push_back(eta);
    }

    if (directions.size() != efficiencies.size())
        throw std::runtime_error("Mismatch between directions and efficiencies");
}

#endif // LOADER_H