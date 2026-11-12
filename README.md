# tkur_libfuzzer (C/C++ and shared Atheris backend)

> Отдельный исходный компонент. Полная Docker-среда, примеры и испытания: [virangle/tkur_fuzzing](https://github.com/virangle/tkur_fuzzing). Команды ниже с путями `components/`, `examples/` и `tests/` выполняются из корня рекурсивно клонированной среды `tkur_fuzzing`.

Самостоятельная сборка: `python3 build.py --install-prefix /opt/tkur/venv` (Linux, Clang/LLVM 18).


A small source patch of LLVM 18.1.8 libFuzzer, **not** a subprocess-log watchdog.
The exact upstream files are vendored and verified offline before every build.
See [provenance and license](UPSTREAM.md).

## Build inside the provided development container

```sh
python3 components/tkur_libfuzzer/build.py --install-prefix /opt/tkur/venv
python3 examples/native/build.py
python3 tests/native/run_tests.py
```

Requires Linux, Python 3, clang++-18 and llvm-ar-18. No Docker build is performed.
Default outputs:

- `components/tkur_libfuzzer/build/libclang_rt.fuzzer.a` (native main included)
- `components/tkur_libfuzzer/build/libclang_rt.fuzzer_no_main.a` (PIC; Atheris)
- `components/tkur_libfuzzer/build/build-info.json` (pin, compiler, flags, SHA256)

`--output DIR` selects another build directory. Optional `--install-prefix PREFIX`
installs `PREFIX/bin/tkur_clang` and `tkur_libfuzzer` wrappers pointing to this
checkout/runtime; keep both at their current locations after installation.

```sh
tkur_clang -std=c++20 examples/native/parser.cpp -o /tmp/parser
# C targets use --c; C++ runtime linkage is included by the wrapper.
tkur_clang --c examples/native/flat.c -o /tmp/flat
tkur_libfuzzer --new-stall 10 --cov-stall=20 -- /tmp/parser corpus/ -timeout=2
# Direct runtime flags work without a launcher:
/tmp/parser corpus/ -new_stall=10 -cov_stall=20 -timeout=2
```

Do **not** link `-fsanitize=fuzzer` at the final link: that would select the
system's unpatched runtime. For manual builds compile with
`-fsanitize=fuzzer-no-link` and link our `libclang_rt.fuzzer.a` plus
`-lstdc++ -pthread -ldl -lrt -lm`. A C object can be linked with clang++-18.
Add `-fsanitize=address` to compile and link if desired. `tkur_clang --coverage`
adds `-fprofile-instr-generate -fcoverage-mapping` for source coverage replay.

## Semantics

- `-new_stall=N`: stop after N **monotonic seconds** without a `NEW` event.
  Feature-only NEW refreshes it; corpus minimization `REDUCE` does not.
- `-cov_stall=N`: stop after N monotonic seconds without growth of total
  observed PC coverage (the native `cov:` number), **not** feature count `ft:`.
- Zero disables that timer. Both enabled means **either** expiration ends fuzzing.
  Durations must be nonnegative decimal int32 values. Raw malformed values,
  fractions, negative values and overflow are rejected, not silently truncated.
- Timers begin after the full initial corpus execution, not process start.
- Checks happen on the fuzzing thread between inputs, including mutation-depth
  iterations. They cannot interrupt a hung callback. Per-input `-timeout=N` is
  unchanged: timeout/crash remains nonzero and saves standard libFuzzer artifacts.
- Normal expiration emits `TKUR: stopping after new-stall ...` or `cov-stall ...`,
  prints standard DONE/final statistics, and **returns 0** from the driver.
  Atheris can then finalize Python/coverage; no stdout/stderr parsing is involved.
- `-fork` plus stall flags is explicitly unsupported (error). Independent
  `-jobs/-workers` each maintain their own timer, not a global campaign timer.
  Merge, minimization, and individual-file replay are not fuzz campaigns and do
  not start these timers. Standard corpus/artifact options stay upstream-compatible.

The exported `TkurLibFuzzerStallAbiVersion()` returns 1 for an explicit patched
backend capability probe. Like upstream, this runtime is **one fuzz session per
process**; repeated LLVMFuzzerRunDriver/Setup/Fuzz invocations are unsupported.
The process-lifetime Fuzzer object intentionally remains allocated, but a normal
loop returns instead of calling exit so an embedding language may shut down.

## Tests and demo replay

`tests/native/run_tests.py` actually compiles and executes C, C++, the real
libFuzzer runtime, and deterministic SanitizerCoverage callbacks. It checks
startup timing, zero/both timers, PC growth, feature-only NEW, REDUCE exclusion,
raw argument rejection, and nonzero timeout/crash artifacts. Synthetic-clock
C++ unit tests additionally cover exact thresholds without scheduling jitter.
Logs and command/elapsed/exit evidence live in `tests/native/build`.

`examples/native/build.py` builds source-coverage-instrumented `flat` (C) and
`parser` (C++) plus corpus directories. Replay uses the standard ABI:

```sh
LLVM_PROFILE_FILE=/tmp/parser-%p.profraw examples/native/build/parser examples/native/build/parser-corpus/branch
```

Source coverage reports are produced by the separate `tkur_coverage` component;
`cov:` itself is an edge/PC metric and is not claimed to be line coverage.
