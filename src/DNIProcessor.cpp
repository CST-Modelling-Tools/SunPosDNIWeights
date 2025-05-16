#include "DNIProcessor.hpp"

#include <fstream>
#include <sstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <stdexcept>

// Cross-platform timegm wrapper
inline std::time_t timegm_utc(std::tm* tm) {
#ifdef _WIN32
    return _mkgmtime(tm);  // Windows: UTC version of mktime
#else
    return timegm(tm);     // POSIX: UTC version of mktime
#endif
}

std::vector<TimedDNI> readDNIFile(const std::string& filepath) {
    std::vector<TimedDNI> data;

    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file: " << filepath << std::endl;
        return data;
    }

    std::string line;
    int line_number = 0;

    while (std::getline(file, line)) {
        ++line_number;
        if (line.empty()) continue;

        std::istringstream ss(line);
        std::string timestamp_str, dni_str;

        if (!std::getline(ss, timestamp_str, ',')) {
            std::cerr << "Warning: Invalid line " << line_number << ": missing timestamp.\n";
            continue;
        }

        if (!std::getline(ss, dni_str)) {
            std::cerr << "Warning: Invalid line " << line_number << ": missing DNI.\n";
            continue;
        }

        std::tm tm = {};
        std::istringstream ts(timestamp_str);
        ts >> std::get_time(&tm, "%Y-%m-%d %H:%M:%S");
        if (ts.fail()) {
            std::cerr << "Warning: Failed to parse time at line " << line_number << ": " << timestamp_str << "\n";
            continue;
        }

        // Convert tm to UTC-based time_point
        std::time_t utc_time = timegm_utc(&tm);
        std::chrono::system_clock::time_point tp = std::chrono::system_clock::from_time_t(utc_time);

        try {
            double dni = std::stod(dni_str);
            data.push_back({tp, dni});
        } catch (const std::invalid_argument&) {
            std::cerr << "Warning: Invalid DNI at line " << line_number << ": " << dni_str << "\n";
        }
    }

    return data;
}