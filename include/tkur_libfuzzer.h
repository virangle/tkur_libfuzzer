/* SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception */
#ifndef TKUR_LIBFUZZER_H
#define TKUR_LIBFUZZER_H
#ifdef __cplusplus
extern "C" {
#endif
/* Returns 1 for a runtime with monotonic NEW/PC stall timers and native aliases.
   Probe only; it does not initialize a fuzzing session. */
int TkurLibFuzzerStallAbiVersion(void);
#ifdef __cplusplus
}
#endif
#endif
