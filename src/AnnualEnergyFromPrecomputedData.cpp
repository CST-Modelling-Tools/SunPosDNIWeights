#include "AnnualEnergyFromPrecomputedData.h"
#include <algorithm>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <iostream>
#include <string>
#include <cmath>

AnnualEnergyFromPrecomputedData::AnnualEnergyFromPrecomputedData(const std::string& filepath)
    : filepath(filepath) {}

double AnnualEnergyFromPrecomputedData::computeAnnualEnergyMWh() const {
    std::ifstream file(filepath);
    if (!file.is_open())
        throw std::runtime_error("Failed to open file: " + filepath);

    std::string line;
    std::getline(file, line);

    // Replace tabs with spaces
    std::replace(line.begin(), line.end(), '\t', ' ');

    double mirrorAreaTotal = 0.0;

    // Parse total mirror area from header line
    auto pos = line.find("mirror_area_total:");
    if (pos != std::string::npos) {
        std::istringstream extract(line.substr(pos + 18)); // length of "mirror_area_total:"
        extract >> mirrorAreaTotal;
    }

    if (mirrorAreaTotal <= 0.0)
        throw std::runtime_error("Invalid or missing mirror_area_total in header.");

    double weightedSum = 0.0;

    // Process each data line
    while (std::getline(file, line)) {
        std::istringstream ss(line);
        double azimuth, elevation, weight, efficiency;
        char comma;

        if (!(ss >> azimuth >> comma >> elevation >> comma >> weight >> comma >> efficiency)) {
            continue; // skip malformed line
        }

        weightedSum += efficiency * weight;
    }

    // Convert to MWh
    return (weightedSum * mirrorAreaTotal) / 1000000.0;
}