#include "AnnualEnergyFromPrecomputedData.h"
#include <iostream>
#include <limits>

int main() {
    const std::string inputFile = "C:/Users/manue_6t240gh/Dropbox/OpenSource/SunPosDNIWeights/data/directions_with_weights_and_efficiency_tarancon_spain.csv";

    try {
        AnnualEnergyFromPrecomputedData calculator(inputFile);
        double energyMWh = calculator.computeAnnualEnergyMWh();

        std::cout << "Estimated annual energy: " << energyMWh << " MWh" << std::endl;
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << std::endl;
        return 1;
    }

    std::cout << "Press Enter to exit...";
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    return 0;
}