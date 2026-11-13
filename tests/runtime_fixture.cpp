// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
// Real libFuzzer callbacks with explicitly registered SanitizerCoverage counters
// make REDUCE, features-only NEW, and PC growth deterministic and independent
// of compiler optimization. Compile this fixture without automatic coverage.
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <thread>
extern "C" void __sanitizer_cov_8bit_counters_init(uint8_t *, uint8_t *);
extern "C" void __sanitizer_cov_pcs_init(const uintptr_t *, const uintptr_t *);
extern "C" void __sanitizer_cov_trace_const_cmp8(uint64_t, uint64_t);
static uint8_t Counters[2];
static uintptr_t PCs[4];
static unsigned Step;
static const char *Mode;
extern "C" int LLVMFuzzerTestOneInput(const uint8_t *, size_t);
extern "C" int LLVMFuzzerInitialize(int *, char ***) {
  Mode = std::getenv("TKUR_FIXTURE");
  if (!Mode) Mode = "flat";
  PCs[0] = reinterpret_cast<uintptr_t>(&LLVMFuzzerTestOneInput);
  PCs[1] = 1;
  PCs[2] = PCs[0] + 1;
  PCs[3] = 0;
  __sanitizer_cov_8bit_counters_init(Counters, Counters + 2);
  __sanitizer_cov_pcs_init(PCs, PCs + 4);
  return 0;
}
extern "C" int LLVMFuzzerTestOneInput(const uint8_t *, size_t) {
  Counters[0] = 1;
  if (!std::strcmp(Mode, "features"))
    __sanitizer_cov_trace_const_cmp8(0, (uint64_t(Step + 1) << 24) | Step);
  if (!std::strcmp(Mode, "pc") && Step >= 5) Counters[1] = 1;
  if (!std::strcmp(Mode, "timeout")) std::this_thread::sleep_for(std::chrono::seconds(5));
  if (!std::strcmp(Mode, "crash")) std::abort();
  if (!std::strcmp(Mode, "slow-init") && !Step)
    std::this_thread::sleep_for(std::chrono::milliseconds(650));
  return 0;
}
extern "C" size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size,
                                          size_t MaxSize, unsigned) {
  std::this_thread::sleep_for(std::chrono::milliseconds(120));
  ++Step;
  if (!std::strcmp(Mode, "reduce")) return Size > 1 ? Size - 1 : 1;
  if (!Size && MaxSize) Size = 1;
  Data[0] = static_cast<uint8_t>(Step);
  return Size;
}
