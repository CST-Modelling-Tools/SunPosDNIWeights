#ifndef DNI_SERIES_H
#define DNI_SERIES_H

#include <vector>
#include <string>
#include <chrono>

class DNISeries {
public:
    explicit DNISeries(const std::string& path);
    std::vector<std::pair<std::chrono::system_clock::time_point, double>> getTimeSeries() const;

private:
    std::vector<std::pair<std::chrono::system_clock::time_point, double>> data;
};

#endif // DNI_SERIES_H