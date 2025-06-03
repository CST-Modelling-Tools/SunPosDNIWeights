#include "AnnualEnergyFromPrecomputedData.h"
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <iostream>

AnnualEnergyFromPrecomputedData::AnnualEnergyFromPrecomputedData(const std::string& filepath)
    : filepath(filepath) {}

void AnnualEnergyFromPrecomputedData::parseFileIfNeeded() {
    if (parsed) return;

    std::ifstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + filepath);
    }

    std::string line;
    int headerLinesRead = 0;

    while (std::getline(file, line)) {
        // Skip empty lines
        if (line.empty()) continue;

        // Parse header lines
        if (line[0] == '#') {
            ++headerLinesRead;

            if (line.find("mirror_area_total:") != std::string::npos) {
                auto pos = line.find("mirror_area_total:");
                if (pos != std::string::npos) {
                    std::istringstream extract(line.substr(pos + 19)); // skip past 'mirror_area_total:'
                    extract >> mirrorAreaTotal;
                    if (mirrorAreaTotal <= 0.0) {
                        throw std::runtime_error("Invalid mirror_area_total in header.");
                    }
                }
            }

            // Skip until we reach the third header line
            if (headerLinesRead < 3) continue;
            else break;
        }
    }

    if (mirrorAreaTotal <= 0.0) {
        throw std::runtime_error("Missing or invalid mirror_area_total in header.");
    }

    // Now read data lines: azimuth_deg, elevation_deg, weight, efficiency
    while (std::getline(file, line)) {
        if (line.empty() || line[0] == '#') continue;

        std::istringstream ss(line);
        double azimuth, elevation, weight, efficiency;
        char comma;

        if (!(ss >> azimuth >> comma >> elevation >> comma >> weight >> comma >> efficiency)) {
            std::cerr << "Warning: Skipping malformed line: " << line << std::endl;
            continue;
        }

        annualDNI += weight; // In Wh/m2 - assuming annual DNI is the sum of weights
        annualEnergy += weight * efficiency * mirrorAreaTotal; //
    }

    parsed = true;
}

double AnnualEnergyFromPrecomputedData::computeAverageEfficiency() const {
    if (!parsed) const_cast<AnnualEnergyFromPrecomputedData*>(this)->parseFileIfNeeded();

    if (annualDNI <= 0.0) {
        throw std::runtime_error("Annual DNI is zero or negative. Cannot compute average efficiency.");
    }

    return annualEnergy / (annualDNI * mirrorAreaTotal); // Efficiency = Energy / (DNI * Area)
}

double AnnualEnergyFromPrecomputedData::computeAnnualEnergyMWh() {
    parseFileIfNeeded();

    return annualEnergy / 1e6; // Convert from Wh to MWh
}