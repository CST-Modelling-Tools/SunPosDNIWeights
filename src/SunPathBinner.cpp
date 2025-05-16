#include "SunPathBinner.hpp"
#include <cmath>
#include <map>
#include <utility>

namespace {

// Convert declination and hour angle (radians) to bin index
std::pair<int, int> getBinIndex(double delta, double omega, double epsilon, double rho, double phi_rad) {
    int n = static_cast<int>(std::floor((delta + epsilon) / rho));
    double omega_max = std::acos(-std::tan(phi_rad) * std::tan(delta));
    int m_max = static_cast<int>(std::round(2 * omega_max / rho));
    double omega_step = 2 * omega_max / m_max;
    int m = static_cast<int>(std::round((omega + omega_max) / omega_step));
    return {n, m};
}

}

// Implementation of the binning algorithm
std::vector<SunPositionSample> computeRepresentativeSamples(
    const std::vector<TimedDNI>& dni_data,
    double latitude_deg,
    int declination_rows)
{
    const double deg_to_rad = M_PI / 180.0;
    const double rad_to_deg = 180.0 / M_PI;
    const double epsilon = 23.44 * deg_to_rad;
    const double phi_rad = latitude_deg * deg_to_rad;
    const double rho = 2 * epsilon / declination_rows;

    // Nested map: bin (n, m) → {sum_DNI, count, sum_az, sum_el}
    struct Accumulator {
        double sum_dni = 0.0;
        int count = 0;
        double sum_azimuth = 0.0;
        double sum_elevation = 0.0;
    };

    std::map<std::pair<int, int>, Accumulator> bins;

    for (const TimedDNI& entry : dni_data) {
        cTime t = entry.time;
        double dni = entry.dni;
        if (dni <= 0.0) continue;

        cSunCoordinates sun = sunpos(t, latitude_deg, 0.0);  // az, el, delta, omega

        // Only consider sun above horizon
        if (sun.dElevation < 0.0) continue;

        double delta = sun.dDeclination * deg_to_rad;
        double omega = sun.dHourAngle * deg_to_rad;
        auto bin_index = getBinIndex(delta, omega, epsilon, rho, phi_rad);

        auto& bin = bins[bin_index];
        bin.sum_dni      += dni;
        bin.count        += 1;
        bin.sum_azimuth  += sun.dAzimuth;
        bin.sum_elevation += sun.dElevation;
    }

    std::vector<SunPositionSample> results;
    for (const auto& [idx, acc] : bins) {
        if (acc.count == 0) continue;
        SunPositionSample s;
        s.azimuth_deg    = acc.sum_azimuth / acc.count;
        s.elevation_deg  = acc.sum_elevation / acc.count;
        s.dni_weight     = acc.sum_dni;
        results.push_back(s);
    }

    return results;
}