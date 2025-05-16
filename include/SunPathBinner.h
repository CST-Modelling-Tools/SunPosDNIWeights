#pragma once

#include "DNIProcessor.hpp" // for TimedDNI
#include "sunpos.h"         // for cTime

#include <vector>

struct SunPositionSample {
    double azimuth_deg;
    double elevation_deg;
    double dni_weight;
};

// Trapezoidal grid sampling in declination and hour angle
std::vector<SunPositionSample> computeRepresentativeSamples(
    const std::vector<TimedDNI>& dni_data,
    double latitude_deg,
    int declination_rows = 3);  // Results in ~27 points (3 declination × 9–11 hour angles)