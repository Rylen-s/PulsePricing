#include "jump_diffusion.hpp"
#include <cmath>
#include <random>

namespace pulserisk {
std::vector<double> simulate_terminal_returns(const SimulationInput& in, unsigned long long seed) {
  std::mt19937_64 rng(seed); std::normal_distribution<double> normal(0., 1.);
  std::poisson_distribution<int> poisson(in.jump_intensity * in.years);
  std::vector<double> returns; returns.reserve(in.paths);
  for (std::size_t i = 0; i < in.paths; ++i) {
    const auto jumps = poisson(rng);
    double jump_sum = 0.;
    for (int j = 0; j < jumps; ++j) jump_sum += in.jump_mean + in.jump_stddev * normal(rng);
    const double log_return = (in.drift - .5 * in.volatility * in.volatility) * in.years + in.volatility * std::sqrt(in.years) * normal(rng) + jump_sum;
    returns.push_back(std::expm1(log_return));
  }
  return returns;
}
}
