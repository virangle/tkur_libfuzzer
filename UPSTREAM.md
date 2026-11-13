# Pinned upstream and licensing

`upstream` preserves the unmodified top-level `compiler-rt/lib/fuzzer` files from
LLVM **llvmorg-18.1.8**, commit
`3b5b5c1ec4a3095ab096dd780e84d7ab81f3d7ff` (annotated tag object
`76caf4176cd7877ad5952737d56da6f515ee4602`). Subdirectories are not needed for
the standalone Linux archive build and are not vendored.

Original source: https://github.com/llvm/llvm-project/tree/llvmorg-18.1.8/compiler-rt/lib/fuzzer

`upstream-manifest.json` retains the original Git blob SHA-1 values, independently
verified when the original source was materialized. `sources.sha256` records
SHA256 of both original `upstream` and checked-in patched `src` files; CMake
verifies every entry offline. It does not need Git, Python, a patching tool, or
network access. Source edits intentionally require updating the reviewed manifest.

`src` is the directly compilable local fork. TKUR changes relative to upstream:

- `FuzzerFlags.def`, `FuzzerOptions.h`: raw stall flags/options;
- `FuzzerInternal.h`, `FuzzerLoop.cpp`, added `TkurStallTimer.h`: monotonic
  NEW-versus-REDUCE and total-PC stall tracking after initial corpus;
- `FuzzerDriver.cpp`: strict int32 stall validation, native long aliases and
  separator, ABI1 probe, normal driver return for embedding-language cleanup.

The original copyright/license notices remain in every source. Complete
compiler-rt **Apache-2.0 WITH LLVM-exception**, including legacy notices, is in
`LICENSE.LLVM.txt`; TKUR additions use the same SPDX license. The binary-only
release includes this required license and the compiled archives, not sources,
scripts, headers or build tools. Build provenance is also available in CMake's
local `BUILD-INFO.txt` and in the release description.

This is a maintained local fork, not an upstream LLVM release artifact.
