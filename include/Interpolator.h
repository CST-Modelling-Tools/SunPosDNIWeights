#ifndef INTERPOLATOR_H
#define INTERPOLATOR_H

#include <vector>
#include <functional>
#include <Eigen/Dense>

class Interpolator {
public:
    Interpolator(const std::vector<Eigen::Vector3d>& sampleDirs,
                 const std::vector<double>& sampleEfficiencies,
                 int polyharmonicOrder,
                 std::function<double(const Eigen::Vector3d)> preconditioner);

    double interpolate(const Eigen::Vector3d& sunDir) const;
    std::vector<std::function<double(const Eigen::Vector3d)>> getLocalizedKernels() const;

private:
    int order;
    std::function<double(const Eigen::Vector3d)> Q;
    std::vector<Eigen::Vector3d> nodes;
    std::vector<double> amplitudes;

    Eigen::MatrixXd kernelMatrix;
    Eigen::MatrixXd kernelMatrixInverse;

    void computeKernelMatrixInverse();
    double kernelFunction(double r) const;
};

#endif // INTERPOLATOR_H