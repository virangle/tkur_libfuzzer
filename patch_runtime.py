# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
"""Exact-context patch of the verified, untouched LLVM 18.1.8 source copy."""
from pathlib import Path
import shutil


def apply(source: Path, helper: Path) -> None:
    def replace(name, old, new):
        path = source / name
        text = path.read_text()
        if text.count(old) != 1:
            raise RuntimeError(f"LLVM pin/context mismatch: {name}: {old!r}")
        path.write_text(text.replace(old, new))

    shutil.copyfile(helper, source / "TkurStallTimer.h")
    replace("FuzzerFlags.def", "FUZZER_FLAG_INT(verbosity, 1,", '''FUZZER_FLAG_INT(new_stall, 0,
    "Stop successfully after N monotonic seconds without NEW (not REDUCE); 0 disables.")
FUZZER_FLAG_INT(cov_stall, 0,
    "Stop successfully after N monotonic seconds without total PC coverage growth; 0 disables.")
FUZZER_FLAG_INT(verbosity, 1,''')
    replace("FuzzerOptions.h", "  int MaxTotalTimeSec = 0;", "  int MaxTotalTimeSec = 0;\n  int NewStallSec = 0;\n  int CovStallSec = 0;")
    replace("FuzzerInternal.h", '#include "FuzzerOptions.h"', '#include "FuzzerOptions.h"\n#include "TkurStallTimer.h"')
    replace("FuzzerInternal.h", "  void AlarmCallback();", "  bool StallExpired();\n  tkur::StallTimer Stall;\n  bool StallStop = false;\n  void AlarmCallback();")
    replace("FuzzerLoop.cpp", "void Fuzzer::MutateAndTestOne() {", '''// TKUR checks only between callbacks: per-input timeout remains independent.
bool Fuzzer::StallExpired() {
  if (StallStop) return true;
  const char *Reason = Stall.Expired(Options.NewStallSec, Options.CovStallSec);
  if (!Reason) return false;
  StallStop = true;
  Printf("TKUR: stopping after %s (new_stall=%d, cov_stall=%d seconds)\\n",
         Reason, Options.NewStallSec, Options.CovStallSec);
  return true;
}

void Fuzzer::MutateAndTestOne() {''')
    replace("FuzzerLoop.cpp", "    MaybeExitGracefully();", "    if (StallExpired()) break;\n    MaybeExitGracefully();")
    replace("FuzzerLoop.cpp", "    TPC.UpdateObservedPCs();", "    TPC.UpdateObservedPCs();\n    Stall.ObserveCoverage(TPC.GetTotalPCCoverage());")
    replace("FuzzerLoop.cpp", '  PrintStatusForNewUnit(U, II->Reduced ? "REDUCE" : "NEW   ");', '  Stall.NewUnit(II->Reduced);\n  PrintStatusForNewUnit(U, II->Reduced ? "REDUCE" : "NEW   ");')
    replace("FuzzerLoop.cpp", "  ReadAndExecuteSeedCorpora(CorporaFiles);", "  ReadAndExecuteSeedCorpora(CorporaFiles);\n  Stall.Start(TPC.GetTotalPCCoverage());")
    replace("FuzzerLoop.cpp", "    if (TimedOut())\n      break;", "    if (TimedOut() || StallExpired())\n      break;")
    replace("FuzzerDriver.cpp", "        auto Val = MyStol(Str);", '''        if (!strcmp(Name, "new_stall") || !strcmp(Name, "cov_stall")) {
          unsigned long Value = 0;
          bool Valid = *Str != 0;
          for (const char *P = Str; *P; ++P) {
            if (*P < '0' || *P > '9' ||
                Value > (static_cast<unsigned long>(INT_MAX) - (*P - '0')) / 10) {
              Valid = false;
              break;
            }
            Value = Value * 10 + (*P - '0');
          }
          if (!Valid) {
            Printf("TKUR: %s requires nonnegative int32 seconds\\n", Name);
            exit(1);
          }
        }
        auto Val = MyStol(Str);''')
    replace("FuzzerDriver.cpp", "  Options.MaxTotalTimeSec = Flags.max_total_time;",  "  Options.MaxTotalTimeSec = Flags.max_total_time;\n  Options.NewStallSec = Flags.new_stall;\n  Options.CovStallSec = Flags.cov_stall;")
    replace("FuzzerDriver.cpp", "  if (Flags.close_fd_mask & 2)", '''  if (Flags.new_stall < 0 || Flags.cov_stall < 0) {
    Printf("TKUR: stall durations must be nonnegative seconds\\n");
    return 1;
  }
  if ((Flags.new_stall || Flags.cov_stall) && Flags.fork) {
    Printf("TKUR: stall timers are unsupported in -fork mode; use independent workers\\n");
    return 1;
  }
  if (Flags.close_fd_mask & 2)''')
    replace("FuzzerDriver.cpp", "  exit(0);  // Don't let F destroy itself.", "  // Keep upstream's process-lifetime F allocation, but let Atheris finalize Python.\n  return 0;")
    replace("FuzzerDriver.cpp", '// Storage for global ExternalFunctions object.', '''extern "C" ATTRIBUTE_INTERFACE int TkurLibFuzzerStallAbiVersion() { return 1; }

// Storage for global ExternalFunctions object.''')
