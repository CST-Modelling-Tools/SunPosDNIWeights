#include "Interpolator.h"
#include "DNISeries.h"
#include "SunPosition.h"
#include "DirectionUtils.h"

#include <iostream>
#include <fstream>
#include <iomanip>
#include <numbers>
#include <Eigen/Dense>

int main(int argc, char* argv[]) {
    if (argc < 5) {
        std::cerr << "Usage: " << argv[0]
                  << " <latitude_deg> <longitude_deg> <dni_input.csv> <output.csv>\n";
        return 1;
    }

    const double latitude_deg = std::stod(argv[1]);
    const double longitude_deg = std::stod(argv[2]); // (currently unused)
    const std::string dniFile = argv[3];
    const std::string outputFile = argv[4];

    constexpr double epsilon_deg = 23.4;   // Obliquity of the ecliptic
    constexpr double rho_deg = 23.4/1.2;   // Angular resolution
    constexpr int polyharmonicOrder = 6;

    const double deg2rad = std::numbers::pi / 180.0;
    const double rad2deg = 180.0 / std::numbers::pi;
    double phi = latitude_deg * deg2rad;
    double epsilon = epsilon_deg * deg2rad;
    double rho = rho_deg * deg2rad;

    // Step 1: Generate sample directions
    std::vector<Eigen::Vector3d> sampleDirs;
    std::vector<double> dummyEffs;

    int N = static_cast<int>(std::round(2 * epsilon / rho));
    double deltaStep = 2 * epsilon / N;

    for (int n = 0; n <= N; ++n) {
        double delta = -epsilon + n * deltaStep;
        double omega_max = std::acos(-std::tan(phi) * std::tan(delta));
        int M = 2 * static_cast<int>(std::round(omega_max / rho));
        double omegaStep = 2 * omega_max / M;

        for (int m = 0; m <= M; ++m) {
            double omega = -omega_max + m * omegaStep;

            double x = -std::sin(omega) * std::cos(delta);
            double y = std::cos(phi) * std::sin(delta) - std::sin(phi) * std::cos(omega) * std::cos(delta);
            double z = std::sin(phi) * std::sin(delta) + std::cos(phi) * std::cos(omega) * std::cos(delta);

            double norm = std::sqrt(x * x + y * y + z * z);
            sampleDirs.emplace_back(x / norm, y / norm, z / norm);
            dummyEffs.push_back(1.0);  // placeholder for interpolator
        }
    }

    // Step 2: Create preconditioned interpolator and get localized kernels
    auto Q = [](const Eigen::Vector3d& r) { return 1.0 + r.z(); };
    Interpolator interpolator(sampleDirs, dummyEffs, polyharmonicOrder, Q);
    auto kernels = interpolator.getLocalizedKernels();

    // Step 3: Load DNI time series and compute weights
    DNISeries dniSeries(dniFile);
    std::vector<double> weights(kernels.size(), 0.0);

    double totalDNI = 0.0;

    for (const auto& [time, dni] : dniSeries.getTimeSeries()) {
        Eigen::Vector3d sunDir = SunPosition::getSunDirection(time, latitude_deg, 0.0);  // longitude ignored here
        if (sunDir.z() <= 0.0) continue;

        totalDNI += dni;
        for (size_t p = 0; p < kernels.size(); ++p)
            weights[p] += dni * kernels[p](sunDir);
    }

    double annualDNI_kWh_per_m2 = totalDNI / 1000.0;


    // Step 4: Output azimuth, elevation, weight to CSV
    std::ofstream out(outputFile);
    out << std::fixed << std::setprecision(6);

    out << "# latitude_deg: " << latitude_deg
        << ", annual_dni_kWh_per_m2: " << annualDNI_kWh_per_m2 << "\n";
    out << "# azimuth_deg, elevation_deg, weight\n";
      
    for (size_t i = 0; i < sampleDirs.size(); ++i) {
        const auto& r = sampleDirs[i];
        double el = std::asin(r.z()) * rad2deg;
        double az = std::atan2(r.x(), r.y()) * rad2deg;
        if (az < 0.0) az += 360.0;
        out << az << ", " << el << ", " << weights[i] << "\n";
    }

    std::cout << "Generated " << sampleDirs.size()
              << " directions with weights to '" << outputFile << "'." << std::endl;

    return 0;
}