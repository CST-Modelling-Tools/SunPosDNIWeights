#ifndef DNI_SERIES_H
#define DNI_SERIES_H

#include <vector>
#include <string>
#include "sunpos.h"  // for cTime

class DNISeries {
public:
    explicit DNISeries(const std::string& path);
    std::vector<std::pair<cTime, double>> getTimeSeries() const;

private:
    std::vector<std::pair<cTime, double>> data;
};

#endif // DNI_SERIES_H