#include "Interpolator.h"
#include "DNISeries.h"
#include "AnnualEnergyCalculator.h"
#include "Loader.h"
#include <iostream>
#include <numbers>

int main() {
    std::vector<Eigen::Vector3d> sampleDirs;
    std::vector<double> efficiencies;
    loadSampledEfficiencies("data/sample_directions_with_efficiency.csv", sampleDirs, efficiencies);
    
    auto Q = [](const Eigen::Vector3d& r) { return 1.0 + r.z(); };
    Interpolator interpolator(sampleDirs, efficiencies, 6, Q);

    DNISeries dniSeries("data/DNI_Seville_2016.csv");
    AnnualEnergyCalculator calculator(interpolator, dniSeries, 37.4117, -6.00583);

    double energy = calculator.computeAnnualEnergy();
    std::cout << "Estimated annual energy (relative units): " << energy << std::endl;
    return 0;
}