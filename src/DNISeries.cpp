#include "DNISeries.h"
#include <fstream>
#include <sstream>
#include <stdexcept>

DNISeries::DNISeries(const std::string& path) 
{
    std::ifstream file(path);
    if (!file) throw std::runtime_error("Could not open DNI file: " + path);

    std::string line;
    while (std::getline(file, line)) {
        std::istringstream ss(line);
        int year, month, day, hour, minute, second;
        char delim;
        double dni;

        if (!(ss >> year >> delim >> month >> delim >> day >> delim >>
                   hour >> delim >> minute >> delim >> second >> delim >> dni)) {
            throw std::runtime_error("Malformed line: " + line);
        }

        cTime time = {
            .iYear = year,
            .iMonth = month,
            .iDay = day,
            .dHours = static_cast<double>(hour),
            .dMinutes = static_cast<double>(minute),
            .dSeconds = static_cast<double>(second)
        };

        data.emplace_back(time, dni);
    }
}

std::vector<std::pair<cTime, double>> DNISeries::getTimeSeries() const {
    return data;
}