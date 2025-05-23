#ifndef LOADER_H
#define LOADER_H

#include <vector>
#include <fstream>
#include <sstream>
#include <Eigen/Dense>

inline std::vector<Eigen::Vector3d> loadSamplingDirections(const std::string& file) {
    std::ifstream in(file);
    std::vector<Eigen::Vector3d> dirs;
    std::string line;
    while (std::getline(in, line)) {
        std::istringstream ss(line);
        double x, y, z;
        char comma;
        ss >> x >> comma >> y >> comma >> z;
        dirs.emplace_back(x, y, z);
    }
    return dirs;
}

inline std::vector<double> loadEfficiencies(const std::string& file) {
    std::ifstream in(file);
    std::vector<double> effs;
    double e;
    while (in >> e) effs.push_back(e);
    return effs;
}

#endif // LOADER_H