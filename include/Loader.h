#ifndef LOADER_H
#define LOADER_H

#include <vector>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <Eigen/Dense>

// Reads lines like: x, y, z, efficiency
inline void loadSampledEfficiencies(
    const std::string& file,
    std::vector<Eigen::Vector3d>& directions,
    std::vector<double>& efficiencies)
{
    std::ifstream in(file);
    if (!in) throw std::runtime_error("Failed to open file: " + file);

    std::string line;
    while (std::getline(in, line)) {
        std::istringstream ss(line);
        double x, y, z, eta;
        char comma;
        if (!(ss >> x >> comma >> y >> comma >> z >> comma >> eta)) {
            throw std::runtime_error("Malformed line: " + line);
        }
        directions.emplace_back(x, y, z);
        efficiencies.push_back(eta);
    }

    if (directions.size() != efficiencies.size())
        throw std::runtime_error("Mismatch between directions and efficiencies");
}

#endif // LOADER_H