/* SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception */
#include <stddef.h>
#include <stdint.h>
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  (void)data; (void)size;
  return 0;
}
