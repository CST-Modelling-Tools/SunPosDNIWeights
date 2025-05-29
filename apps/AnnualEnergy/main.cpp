#include "AnnualEnergyFromPrecomputedData.h"
#include <iostream>
#include <fstream>
#include <iomanip>

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <input_csv> <output_csv>" << std::endl;
        return 1;
    }

    const std::string inputFile = argv[1];
    const std::string outputFile = argv[2];

    try {
        AnnualEnergyFromPrecomputedData calculator(inputFile);
        double energyMWh = calculator.computeAnnualEnergyMWh();
        double avgEfficiency = calculator.computeAverageEfficiency();

        std::cout << "Estimated annual energy: " << energyMWh << " MWh" << std::endl;
        std::cout << "Average optical efficiency: " << avgEfficiency << std::endl;

        // Save results to output file
        std::ofstream out(outputFile);
        if (!out) throw std::runtime_error("Failed to open output file: " + outputFile);

        out << std::fixed << std::setprecision(6);
        out << "annual_energy_MWh," << energyMWh << "\n";
        out << "average_optical_efficiency," << avgEfficiency << "\n";

        out.close();
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << std::endl;
        return 1;
    }

    return 0;
}