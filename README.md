# SunPositionDNIWeights

This C++ project computes a reduced set of representative sun positions (azimuth and elevation) and associated DNI weights from an annual DNI time series.

## Features

- Accepts `{timestamp, DNI}` input (hourly resolution).
- Computes sun positions (using high-precision algorithm).
- Performs trapezoidal binning in (declination, hour angle) space.
- Outputs ~30 representative positions in azimuth/elevation with associated DNI weights.

## Build

```bash
mkdir build && cd build
cmake ..
make
