# Pinned upstream and licensing

Vendored directory `upstream` contains the unmodified top-level files of
`compiler-rt/lib/fuzzer` from LLVM **llvmorg-18.1.8**, commit
`3b5b5c1ec4a3095ab096dd780e84d7ab81f3d7ff` (annotated tag object
`76caf4176cd7877ad5952737d56da6f515ee4602`). Subdirectories/tests are not needed
for the Linux standalone archive build and are not vendored.

Source: https://github.com/llvm/llvm-project/tree/llvmorg-18.1.8/compiler-rt/lib/fuzzer

`upstream-manifest.json` records each original Git blob SHA-1 from the public
GitHub directory API. `build.py` checks the Git object hash of **every** original
file before applying exact-context modifications to a build-only copy. A mirror
was used for retrieval (cdn.jsdelivr.net/gh/llvm/llvm-project@llvmorg-18.1.8),
with missing files obtained through the public Git blob API. No credentials.

Original LLVM copyright notices remain in all sources. Complete compiler-rt
Apache-2.0 WITH LLVM-exception license (including legacy notices) is in
`LICENSE.LLVM.txt`. TKUR additions use the same SPDX license. Modified-file
logic is explicitly identified in `patch_runtime.py`; vendored sources remain
untouched. Build archives are accompanied by a license copy and build metadata.

This is a maintained local patch, not an upstream LLVM release artifact.
