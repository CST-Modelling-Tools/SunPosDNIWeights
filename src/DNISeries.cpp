#include "DNISeries.h"
#include <fstream>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <ctime>

DNISeries::DNISeries(const std::string& path) {
    std::ifstream file(path);
    std::string line;
    while (std::getline(file, line)) {
        std::istringstream ss(line);
        int year, month, day, hour, minute, second;
        char delim;
        double dni;
        ss >> year >> delim >> month >> delim >> day >> delim >> hour >> delim >> minute >> delim >> second >> delim >> dni;
        std::tm tm = { .tm_sec = second, .tm_min = minute, .tm_hour = hour, .tm_mday = day,
                       .tm_mon = month - 1, .tm_year = year - 1900 };
        auto tp = std::chrono::system_clock::from_time_t(std::mktime(&tm));
        data.emplace_back(tp, dni);
    }
}

std::vector<std::pair<std::chrono::system_clock::time_point, double>> DNISeries::getTimeSeries() const {
    return data;
}