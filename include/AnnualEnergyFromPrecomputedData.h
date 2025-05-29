#ifndef ANNUAL_ENERGY_FROM_PRECOMPUTED_DATA_H
#define ANNUAL_ENERGY_FROM_PRECOMPUTED_DATA_H

#include <string>

class AnnualEnergyFromPrecomputedData {
public:
    explicit AnnualEnergyFromPrecomputedData(const std::string& filepath);

    double computeAnnualEnergyMWh();
    double computeAverageEfficiency() const;

private:
    std::string filepath;

    double mirrorAreaTotal = 0.0;
    double weightedEfficiencySum = 0.0;
    double totalWeight = 0.0;

    bool parsed = false;

    void parseFileIfNeeded();
};

#endif // ANNUAL_ENERGY_FROM_PRECOMPUTED_DATA_H