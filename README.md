# tkur_libfuzzer 0.2.0 — native C/C++ libFuzzer

Pinned LLVM **18.1.8** with monotonic NEW/PC-coverage stall timers. Build and run
with **CMake and Clang 18 only**: no Python, shell launcher, interpreter, or
subprocess log watchdog is required. CLI aliases are parsed by the C++ runtime
inside your compiled fuzz target.

## Build from this standalone repository

Linux, CMake >=3.22, Clang/LLVM 18, C++ standard library and POSIX threads:

```sh
cmake -S . -B build -DCMAKE_C_COMPILER=clang-18 \
  -DCMAKE_CXX_COMPILER=clang++-18 -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j
# Optional developer install: libraries, public headers, license/build metadata.
cmake --install build --prefix /opt/tkur-native
```

Outputs (both PIC):

- `build/libclang_rt.fuzzer.a` — libFuzzer including native `main`;
- `build/libclang_rt.fuzzer_no_main.a` — embedding/Atheris backend, no `main`.

Every configure verifies SHA256 hashes of the vendored original source and the
checked-in patched C++ source. No network or code generator is used.
[Provenance and licensing](UPSTREAM.md) describe the exact upstream commit.

## Binary release

The Linux x86-64 release archive contains **only the two compiled `.a` libraries
and the required LLVM license**. It contains no Python, shell scripts, CMake,
headers, sources or demo executables. Download/extract it and link a target using
the archive path, as below. Binary artifacts built on Ubuntu 24.04 use its
Clang 18/libstdc++/glibc 2.39 environment; compatibility with older glibc systems
is not claimed. Static libFuzzer archives do not statically link libc/libstdc++
into your executable. Rebuild from source for a different target environment.

A source checkout can produce the same package layout with:

```sh
cmake --build build --target package
```

## Compile and link your C++ target

```cpp
// target.cpp
#include <cstddef>
#include <cstdint>
extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  // Exercise the real parser or library here.
  (void)data; (void)size;
  return 0;
}
```

```sh
clang++-18 -g -O1 -fsanitize=fuzzer-no-link target.cpp \
  build/libclang_rt.fuzzer.a -pthread -ldl -o target
mkdir -p corpus
printf seed > corpus/seed
./target --new-stall 10 --cov-stall=20 -timeout=2 corpus
# Raw upstream-style flags are equivalent:
./target -new_stall=10 -cov_stall=20 -timeout=2 corpus
```

For C, implement the same callback without `extern "C"`, compile with `clang-18`,
then link the object using `clang++-18`:

```sh
clang-18 -g -O1 -fsanitize=fuzzer-no-link -c target.c -o target.o
clang++-18 target.o build/libclang_rt.fuzzer.a -pthread -ldl -o target-c
./target-c --new-stall=10 corpus
```

**Do not use `-fsanitize=fuzzer` at the final link:** it selects the system's
unpatched runtime. To enable ASan, additionally pass `-fsanitize=address` while
compiling **and** linking. To obtain source-coverage profiles add
`-fprofile-instr-generate -fcoverage-mapping`; this is separate from the runtime
PC `cov:` metric, which is not line coverage.

## Native options and semantics

- `--new-stall N`, `--new-stall=N`, or `-new_stall=N`: successful stop after N
  monotonic seconds without a `NEW` event. Feature-only NEW refreshes the timer;
  corpus minimization `REDUCE` does **not**.
- `--cov-stall N`, `--cov-stall=N`, or `-cov_stall=N`: successful stop after N
  monotonic seconds without growth of total observed PCs (`cov:`), not `ft:`.
- `0` disables a timer; both enabled means **either** expiry stops fuzzing.
  Values must be nonnegative decimal int32 seconds. Empty/missing/malformed,
  fractional, signed/negative and overflow values are rejected.
- Options are applied left-to-right; the **last occurrence wins**, including
  mixes of raw flags and aliases. `--` ends option parsing: everything after it
  is an input path (including a filename that looks like a flag).
- Unknown flags keep upstream libFuzzer behavior: unknown single-dash flags
  warn and are ignored; unknown long flags are ignored/pass-through, not rejected.
- Timers start after initial corpus execution, use `std::chrono::steady_clock`,
  and are checked between target callbacks and mutation-depth iterations.
  They cannot interrupt a hung callback. `-timeout=N` remains the separate
  per-input failure watchdog: timeout/crash returns nonzero and saves artifacts.
- Expiration emits `TKUR: stopping after new-stall ...` or `cov-stall ...`, prints
  standard DONE/statistics and **returns 0** from `LLVMFuzzerRunDriver`.
- `-fork` with a stall timer is explicitly unsupported. Independent jobs/workers
  each own a timer, not a global campaign timer. Individual-file replay, merge,
  and minimization are not fuzz campaigns and do not start stall timers.

## Embedding and Atheris

Link the PIC `libclang_rt.fuzzer_no_main.a` into the embedding runtime. Exported
`extern "C" int TkurLibFuzzerStallAbiVersion(void)` returns **1**, unchanged from
0.1.x, for explicit capability probing. Normal fuzz-loop shutdown returns to
its embedding caller (so Atheris can finalize Python); no exit/log parsing is
needed. Like upstream, only **one fuzz session per process** is supported.
Atheris still requires Python for Python targets; C/C++ targets do not.

## Actual C/C++ tests (no Python needed)

```sh
cmake -S . -B build -DCMAKE_C_COMPILER=clang-18 \
  -DCMAKE_CXX_COMPILER=clang++-18 -DTKUR_BUILD_TESTS=ON
cmake --build build -j
ctest --test-dir build --output-on-failure
```

Optional tests are never installed or packaged. They compile real C/C++ fuzz
binaries, execute native aliases, check last-wins/0/separator/malformed inputs,
feature-only NEW at constant PC coverage, REDUCE exclusion, initial corpus
startup, PC growth, and preserve actual timeout/crash failures and artifacts.
The synthetic-clock C++ timer unit test covers exact monotonic thresholds.
Detailed runtime logs are in `build/tests/regressions`.
