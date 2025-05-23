#include "Interpolator.h"
#include <cmath>
#include <stdexcept>

Interpolator::Interpolator(const std::vector<Eigen::Vector3d>& sampleDirs,
                           const std::vector<double>& sampleEfficiencies,
                           int polyharmonicOrder,
                           std::function<double(const Eigen::Vector3d)> preconditioner)
    : order(polyharmonicOrder), Q(std::move(preconditioner)), nodes(sampleDirs) {
    if (sampleDirs.size() != sampleEfficiencies.size())
        throw std::runtime_error("Mismatch in number of directions and efficiencies");

    const int N = static_cast<int>(sampleDirs.size());
    kernelMatrix.resize(N, N);

    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j)
            kernelMatrix(i, j) = kernelFunction((sampleDirs[i] - sampleDirs[j]).norm());

    Eigen::VectorXd fVec(N);
    for (int i = 0; i < N; ++i)
        fVec(i) = sampleEfficiencies[i] * Q(sampleDirs[i]);

    computeKernelMatrixInverse();
    Eigen::VectorXd aVec = kernelMatrixInverse * fVec;
    amplitudes = std::vector<double>(aVec.data(), aVec.data() + aVec.size());
}

double Interpolator::interpolate(const Eigen::Vector3d& sunDir) const {
    double sum = 0.0;
    for (size_t i = 0; i < nodes.size(); ++i)
        sum += amplitudes[i] * kernelFunction((sunDir - nodes[i]).norm());
    return sum / Q(sunDir);
}

std::vector<std::function<double(const Eigen::Vector3d)>> Interpolator::getLocalizedKernels() const {
    std::vector<std::function<double(const Eigen::Vector3d)>> localKernels;
    for (size_t p = 0; p < nodes.size(); ++p) {
        localKernels.push_back([=](const Eigen::Vector3d& r) {
            double sum = 0.0;
            for (size_t q = 0; q < nodes.size(); ++q)
                sum += kernelMatrixInverse(p, q) * kernelFunction((r - nodes[q]).norm());
            return Q(nodes[p]) / Q(r) * sum;
        });
    }
    return localKernels;
}

void Interpolator::computeKernelMatrixInverse() {
    kernelMatrixInverse = kernelMatrix.inverse();
}

double Interpolator::kernelFunction(double r) const {
    if (r == 0.0) return 0.0;
    return (order % 2 == 1) ? std::pow(r, order) : std::pow(r, order) * std::log(r);
}