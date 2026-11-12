#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
"""Compile/link with the TKUR runtime, never the system's unpatched fuzzer."""
import argparse
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--runtime", type=Path, default=Path(__file__).resolve().parent / "build")
    parser.add_argument("--c", action="store_true", help="compile C instead of C++")
    parser.add_argument("--help", action="store_true")
    options, args = parser.parse_known_args()
    if options.help:
        print("usage: tkur_clang [--c] [--runtime DIR] [--coverage] CLANG_ARGS...\n"
              "Links patched libFuzzer. --coverage adds source-based LLVM coverage.\n"
              "For C: compile with --c -c then link the object without --c.")
        return 0
    coverage = "--coverage" in args
    args = [a for a in args if a != "--coverage"]
    if not args:
        parser.error("compiler arguments required")
    if any("-fsanitize=fuzzer" in a for a in args):
        parser.error("do not supply -fsanitize=fuzzer; wrapper selects patched runtime")
    command = [os.environ.get("CC" if options.c else "CXX", "clang-18" if options.c else "clang++-18"),
               "-g", "-O1", "-fno-omit-frame-pointer", "-fsanitize=fuzzer-no-link"]
    if coverage:
        command += ["-fprofile-instr-generate", "-fcoverage-mapping"]
    command += args
    if not any(a in args for a in ["-c", "-S", "-E"]):
        archive = options.runtime.resolve() / "libclang_rt.fuzzer.a"
        if not archive.is_file():
            parser.error(f"missing patched runtime: {archive}; run build.py")
        command += [str(archive), "-lstdc++", "-pthread", "-ldl", "-lrt", "-lm"]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
