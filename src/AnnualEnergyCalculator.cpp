#include "AnnualEnergyCalculator.h"
#include "SunPosition.h"

AnnualEnergyCalculator::AnnualEnergyCalculator(const Interpolator& interp,
                                               const DNISeries& dni,
                                               double lat, double lon)
    : interpolator(interp), dniSeries(dni), latitude(lat), longitude(lon) {}

double AnnualEnergyCalculator::computeAnnualEnergy() {
    double total = 0.0;
    for (const auto& [time, dni] : dniSeries.getTimeSeries()) {
        Eigen::Vector3d sunDir = SunPosition::getSunDirection(time, latitude, longitude);
        if (sunDir.z() <= 0.0) continue;
        total += interpolator.interpolate(sunDir) * dni;
    }
    return total;
}