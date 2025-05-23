#ifndef ANNUAL_ENERGY_CALCULATOR_H
#define ANNUAL_ENERGY_CALCULATOR_H

#include "Interpolator.h"
#include "DNISeries.h"

class AnnualEnergyCalculator {
public:
    AnnualEnergyCalculator(const Interpolator& interp, const DNISeries& dni, double lat, double lon);
    double computeAnnualEnergy();

private:
    const Interpolator& interpolator;
    const DNISeries& dniSeries;
    double latitude, longitude;
};

#endif // ANNUAL_ENERGY_CALCULATOR_H