#ifndef ANNUAL_ENERGY_FROM_PRECOMPUTED_DATA_H
#define ANNUAL_ENERGY_FROM_PRECOMPUTED_DATA_H

#include <string>

class AnnualEnergyFromPrecomputedData {
public:
    explicit AnnualEnergyFromPrecomputedData(const std::string& filepath);

    double computeAnnualEnergyMWh() const;

private:
    std::string filepath;
};

#endif // ANNUAL_ENERGY_FROM_PRECOMPUTED_DATA_H
