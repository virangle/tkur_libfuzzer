#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
"""Build the vendored, integrity-checked LLVM 18.1.8 libFuzzer fork (Linux)."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from patch_runtime import apply

ROOT = Path(__file__).resolve().parent
PIN = "3b5b5c1ec4a3095ab096dd780e84d7ab81f3d7ff"


def verify():
    for item in json.loads((ROOT / "upstream-manifest.json").read_text(encoding="utf-8-sig")):
        data = (ROOT / "upstream" / item["name"]).read_bytes()
        digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if digest != item["git_blob_sha1"]:
            raise RuntimeError(f"Upstream integrity failure: {item['name']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build")
    parser.add_argument("--install-prefix", type=Path)
    parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 1, 8))
    args = parser.parse_args()
    verify()
    cxx = os.environ.get("CXX", "clang++-18")
    version = subprocess.check_output([cxx, "--version"], text=True)
    if "clang version 18." not in version:
        raise RuntimeError("clang++ 18 required (set CXX to its path)")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = output / "src"
    source.mkdir(exist_ok=True)
    for path in (ROOT / "upstream").iterdir():
        shutil.copyfile(path, source / path.name)
    apply(source, ROOT / "stall_timer.h")
    objdir = output / "obj"
    objdir.mkdir(exist_ok=True)
    # Same translation units as upstream standalone build. Interceptors are
    # intentionally not linked: this is the Linux weak-symbol runtime.
    sources = sorted(p for p in source.glob("Fuzzer*.cpp") if p.name != "FuzzerInterceptors.cpp")
    flags = ["-std=c++17", "-O2", "-g", "-fPIC", "-fno-omit-frame-pointer", "-pthread",
             "-fno-sanitize=all", "-fno-sanitize-coverage=trace-pc-guard,trace-cmp,inline-8bit-counters,pc-table",
             f"-ffile-prefix-map={output}=tkur-libfuzzer-build"]

    def compile_one(path):
        obj = objdir / (path.stem + ".o")
        subprocess.run([cxx, *flags, "-c", str(path), "-o", str(obj)], check=True)
        return obj

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        objects = list(pool.map(compile_one, sources))
    ar = os.environ.get("AR", "llvm-ar-18")
    # Fresh archive prevents obsolete members after upstream changes.
    for name, members in [("libclang_rt.fuzzer_no_main.a", [p for p in objects if p.stem != "FuzzerMain"]),
                          ("libclang_rt.fuzzer.a", objects)]:
        archive = output / name
        if archive.exists():
            archive.unlink()
        subprocess.run([ar, "rcsD", str(archive), *map(str, members)], check=True)
        shutil.copyfile(ROOT / "LICENSE.LLVM.txt", output / "LICENSE.LLVM.txt")
        print(archive, flush=True)
    metadata = {"llvm_commit": PIN, "llvm_tag": "llvmorg-18.1.8", "compiler": version,
                "flags": flags, "stall_abi": 1,
                "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob("*.a")}}
    (output / "build-info.json").write_text(json.dumps(metadata, indent=2) + "\n")
    if args.install_prefix:
        bindir = args.install_prefix.resolve() / "bin"
        bindir.mkdir(parents=True, exist_ok=True)
        for name, script, extra in [("tkur_libfuzzer", "launcher.py", []),
                                    ("tkur_clang", "compiler.py", ["--runtime", str(output)])]:
            command = [sys.executable, str(ROOT / script), *extra]
            wrapper = bindir / name
            wrapper.write_text("#!/bin/sh\nexec " + shlex.join(command) + ' "$@"\n')
            wrapper.chmod(0o755)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
