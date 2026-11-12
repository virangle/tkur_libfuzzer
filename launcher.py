#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
"""Run a TKUR-linked fuzz binary with long stall aliases (no log parsing)."""
import argparse
import os
import re
import sys


def normalize(arguments):
    result = []
    i = 0
    while i < len(arguments):
        arg = arguments[i]
        for alias, native in [("--new-stall", "new_stall"), ("--cov-stall", "cov_stall")]:
            if arg == alias or arg.startswith(alias + "="):
                if "=" in arg:
                    value = arg.split("=", 1)[1]
                else:
                    i += 1
                    if i >= len(arguments):
                        raise ValueError(f"{alias} requires nonnegative integer seconds")
                    value = arguments[i]
                if not re.fullmatch(r"[0-9]+", value) or int(value) > 2147483647:
                    raise ValueError(f"{alias} requires nonnegative int32 seconds")
                result.append(f"-{native}={value}")
                break
        else:
            result.append(arg)
        i += 1
    return result


def main():
    # Aliases may occur before or after the executable; leave all native flags intact.
    if not sys.argv[1:] or sys.argv[1:] == ["--help"]:
        print("usage: tkur_libfuzzer [--new-stall N] [--cov-stall N] [--] BINARY [FUZZER_ARGS...]")
        return 0
    try:
        args = normalize(sys.argv[1:])
    except ValueError as error:
        print(f"tkur_libfuzzer: {error}", file=sys.stderr)
        return 2
    options = []
    while args and (args[0].startswith("-new_stall=") or args[0].startswith("-cov_stall=")):
        options.append(args.pop(0))
    if args and args[0] == "--":
        args.pop(0)
    if not args:
        print("tkur_libfuzzer: binary is required", file=sys.stderr)
        return 2
    binary, *rest = args
    os.execvp(binary, [binary, *options, *rest])


if __name__ == "__main__":
    raise SystemExit(main())
