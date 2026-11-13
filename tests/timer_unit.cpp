// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
#include "TkurStallTimer.h"
#include <cassert>
#include <chrono>
#include <cstring>
using namespace std::chrono;
int main() {
  tkur::StallTimer timer;
  const auto start = tkur::StallTimer::Time{};
  assert(!timer.Expired(1, 1, start + hours(1))); // not active during startup
  timer.Start(10, start);
  assert(!timer.Expired(0, 0, start + hours(1))); // both disabled
  timer.NewUnit(true, start + milliseconds(900)); // REDUCE must not reset
  assert(!strcmp(timer.Expired(1, 0, start + seconds(1)), "new-stall"));
  timer.NewUnit(false, start + milliseconds(900));
  assert(!timer.Expired(1, 0, start + seconds(1)));
  timer.ObserveCoverage(10, start + milliseconds(900)); // ft-only / unchanged PCs
  assert(!strcmp(timer.Expired(0, 1, start + seconds(1)), "cov-stall"));
  timer.ObserveCoverage(11, start + milliseconds(900));
  assert(!timer.Expired(0, 1, start + seconds(1)));
  assert(!strcmp(timer.Expired(5, 1, start + seconds(2)), "cov-stall"));
  assert(!strcmp(timer.Expired(1, 5, start + seconds(2)), "new-stall"));
}
