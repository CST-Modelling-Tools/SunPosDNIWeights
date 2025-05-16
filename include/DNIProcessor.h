#pragma once

#include <vector>
#include <string>
#include <chrono>

#include "sunpos.h"

struct TimedDNI {
    cTime time;
    double dni;
};

// Reads a CSV with format: "YYYY-MM-DD HH:MM:SS,DNI"
std::vector<TimedDNI> readDNIFile(const std::string& filepath);