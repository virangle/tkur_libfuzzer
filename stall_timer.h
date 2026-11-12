// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
// TKUR additions, 2026. This helper has no target instrumentation or I/O.
#ifndef TKUR_STALL_TIMER_H
#define TKUR_STALL_TIMER_H
#include <chrono>
#include <cstddef>
namespace tkur {
class StallTimer {
 public:
  using Clock = std::chrono::steady_clock;
  using Time = Clock::time_point;
  void Start(std::size_t PCs, Time Now = Clock::now()) {
    Active = true; Coverage = PCs; LastNew = LastCov = Now;
  }
  void NewUnit(bool Reduced, Time Now = Clock::now()) {
    if (Active && !Reduced) LastNew = Now;
  }
  void ObserveCoverage(std::size_t PCs, Time Now = Clock::now()) {
    if (Active && PCs > Coverage) { Coverage = PCs; LastCov = Now; }
  }
  const char *Expired(int NewSeconds, int CovSeconds,
                      Time Now = Clock::now()) const {
    if (!Active) return nullptr;
    if (NewSeconds > 0 && Now - LastNew >= std::chrono::seconds(NewSeconds))
      return "new-stall";
    if (CovSeconds > 0 && Now - LastCov >= std::chrono::seconds(CovSeconds))
      return "cov-stall";
    return nullptr;
  }
 private:
  bool Active = false;
  std::size_t Coverage = 0;
  Time LastNew{}, LastCov{};
};
}  // namespace tkur
#endif
