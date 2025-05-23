#include <iostream>
#include <fstream>
#include <cmath>
#include <vector>
#include <iomanip>
#include <numbers>

struct Direction {
    double azimuth_deg;   // From North toward East
    double elevation_deg; // Above horizon
};

// Compute omega_max(δ) = arccos(-tan(φ) * tan(δ))
double omegaMax(double delta, double phi) {
    double arg = -std::tan(phi) * std::tan(delta);
    if (arg <= -1.0) return std::numbers::pi;
    if (arg >= 1.0) return 0.0;
    return std::acos(arg);
}

int main() {
    constexpr double latitude_deg = 37.4117;
    constexpr double epsilon_deg = 23.4;
    constexpr double rho_deg = 23.4;
    const std::string outputPath = "data/sample_directions_tonatiuh.csv";

    const double deg2rad = std::numbers::pi / 180.0;
    const double rad2deg = 180.0 / std::numbers::pi;

    double phi = latitude_deg * deg2rad;
    double epsilon = epsilon_deg * deg2rad;
    double rho = rho_deg * deg2rad;

    int N = static_cast<int>(std::round(2 * epsilon / rho));
    double deltaStep = 2 * epsilon / N;

    std::vector<Direction> directions;

    for (int n = 0; n <= N; ++n) {
        double delta = -epsilon + n * deltaStep;
        double omega_max = omegaMax(delta, phi);
        int M = 2 * static_cast<int>(std::round(omega_max / rho));
        double omegaStep = 2 * omega_max / M;

        for (int m = 0; m <= M; ++m) {
            double omega = -omega_max + m * omegaStep;

            // Local sun vector (ENZ frame)
            double x = -std::sin(omega) * std::cos(delta);
            double y = std::cos(phi) * std::sin(delta) - std::sin(phi) * std::cos(omega) * std::cos(delta);
            double z = std::sin(phi) * std::sin(delta) + std::cos(phi) * std::cos(omega) * std::cos(delta);

            double norm = std::sqrt(x * x + y * y + z * z);
            x /= norm; y /= norm; z /= norm;

            // Convert to azimuth (from North to East) and elevation (above horizon)
            double elevation = std::asin(z) * rad2deg;
            double azimuth = std::atan2(x, y) * rad2deg;
            if (azimuth < 0.0) azimuth += 360.0;

            directions.push_back({ azimuth, elevation });
        }
    }

    std::ofstream out(outputPath);
    out << std::fixed << std::setprecision(6);
    out << "# azimuth [deg], elevation [deg]\n";
    for (const auto& dir : directions)
        out << dir.azimuth_deg << ", " << dir.elevation_deg << "\n";

    std::cout << "Saved " << directions.size()
              << " directions to " << outputPath << std::endl;

    return 0;
}