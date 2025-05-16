#include "DNIProcessor.hpp"

#include <fstream>
#include <sstream>
#include <iostream>
#include <string>

std::vector<TimedDNI> readDNIFile(const std::string& filepath) {
    std::vector<TimedDNI> data;
    std::ifstream file(filepath);

    if (!file.is_open()) {
        std::cerr << "Error: Could not open DNI file: " << filepath << std::endl;
        return data;
    }

    std::string line;
    int line_number = 0;

    while (std::getline(file, line)) {
        ++line_number;
        if (line.empty()) continue;

        std::istringstream ss(line);
        std::string year_str, month_str, day_str, hour_str, minute_str, dni_str;

        // Expected CSV format: Year,Month,Day,Hour,Minute,DNI
        if (!std::getline(ss, year_str, ',')) continue;
        if (!std::getline(ss, month_str, ',')) continue;
        if (!std::getline(ss, day_str, ',')) continue;
        if (!std::getline(ss, hour_str, ',')) continue;
        if (!std::getline(ss, minute_str, ',')) continue;
        if (!std::getline(ss, dni_str)) continue;

        try {
            cTime ct;
            ct.iYear    = std::stoi(year_str);
            ct.iMonth   = std::stoi(month_str);
            ct.iDay     = std::stoi(day_str);
            ct.dHours   = static_cast<double>(std::stoi(hour_str));
            ct.dMinutes = static_cast<double>(std::stoi(minute_str));
            ct.dSeconds = 0.0;

            double dni = std::stod(dni_str);
            data.push_back({ct, dni});
        }
        catch (const std::exception& e) {
            std::cerr << "Warning: Invalid data at line " << line_number << ": " << e.what() << "\n";
        }
    }

    return data;
}