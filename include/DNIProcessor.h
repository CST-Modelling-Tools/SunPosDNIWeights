#pragma once

#include <vector>
#include <string>
#include <chrono>

struct TimedDNI {
    std::chrono::system_clock::time_point time;
    double dni;
};

// Reads a CSV with format: "YYYY-MM-DD HH:MM:SS,DNI"
std::vector<TimedDNI> readDNIFile(const std::string& filepath);