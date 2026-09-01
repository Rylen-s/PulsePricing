#pragma once
#include <cstddef>
#include <vector>

namespace pulserisk {
struct SimulationInput { double drift, volatility, jump_intensity, jump_mean, jump_stddev, years; std::size_t paths; };
std::vector<double> simulate_terminal_returns(const SimulationInput& input, unsigned long long seed);
}
