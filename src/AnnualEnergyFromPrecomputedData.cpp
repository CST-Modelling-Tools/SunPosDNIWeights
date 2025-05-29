#include "AnnualEnergyFromPrecomputedData.h"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>

void AnnualEnergyFromPrecomputedData::parseFileIfNeeded() {
    if (parsed) return;

    std::ifstream file(filepath);
    if (!file.is_open())
        throw std::runtime_error("Failed to open file: " + filepath);

    std::string line;
    std::getline(file, line);
    std::replace(line.begin(), line.end(), '\t', ' ');

    // Parse total mirror area from header
    auto pos = line.find("mirror_area_total:");
    if (pos != std::string::npos) {
        std::istringstream extract(line.substr(pos + 18));
        extract >> mirrorAreaTotal;
    }

    if (mirrorAreaTotal <= 0.0)
        throw std::runtime_error("Invalid or missing mirror_area_total in header.");

    // Read data lines
    while (std::getline(file, line)) {
        std::istringstream ss(line);
        double azimuth, elevation, weight, efficiency;
        char comma;

        if (!(ss >> azimuth >> comma >> elevation >> comma >> weight >> comma >> efficiency))
            continue;

        weightedEfficiencySum += efficiency * weight;
        totalWeight += weight;
    }

    parsed = true;
}

AnnualEnergyFromPrecomputedData::AnnualEnergyFromPrecomputedData(const std::string& filepath)
    : filepath(filepath) {}

double AnnualEnergyFromPrecomputedData::computeAnnualEnergyMWh() {
    parseFileIfNeeded();

    return (weightedEfficiencySum * mirrorAreaTotal) / 1e6; // W to MWh
}

double AnnualEnergyFromPrecomputedData::computeAverageEfficiency() const {
    if (totalWeight <= 0.0)
        throw std::runtime_error("No data available or zero total weight.");

    return weightedEfficiencySum / totalWeight;
}