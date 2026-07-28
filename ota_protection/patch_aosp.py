#!/usr/bin/env python3
"""Minimal patch: fix bmlutils build error only.

applypatch.cpp has `#include "bmlutils/bmlutils.h"` but the AOSP
bootable/recovery tree has no bmlutils project. A double-quote #include
resolves relative to the source file's own directory first, so we just
drop an empty stub header at applypatch/bmlutils/bmlutils.h.

We deliberately do NOT touch Android.bp include_dirs: soong treats those
entries as relative-to-module-source-path and prepends them, producing a
bogus path like "bootable/recovery/applypatch/bootable/recovery" that
fails the soong bootstrap. A sibling stub header is the clean fix.

OTA partition protection is intentionally NOT applied here. This script
only fixes the compilation error.
"""

import os
import sys

RECOVERY_DIR = sys.argv[1] if len(sys.argv) > 1 else "bootable/recovery"

# ============================================================
# Create empty bmlutils/bmlutils.h stub next to applypatch.cpp
# applypatch.cpp does `#include "bmlutils/bmlutils.h"`. With double quotes
# the compiler looks in the source file's directory first, so a stub at
# applypatch/bmlutils/bmlutils.h satisfies the include. applypatch doesn't
# call any bmlutils symbol, so an empty header links fine too.
# ============================================================
stub = (
    "#ifndef BMLUTILS_H_\n"
    "#define BMLUTILS_H_\n"
    "/* Empty stub: bmlutils project not present in this tree. */\n"
    "/* applypatch only #includes the header; no symbol is referenced. */\n"
    "#endif  // BMLUTILS_H_\n"
)

created = []
for base in ("applypatch", "updater"):
    hdir = os.path.join(RECOVERY_DIR, base, "bmlutils")
    hfile = os.path.join(hdir, "bmlutils.h")
    if not os.path.isfile(hfile):
        os.makedirs(hdir, exist_ok=True)
        with open(hfile, "w") as f:
            f.write(stub)
        created.append(f"{base}/bmlutils/bmlutils.h")

if created:
    print("OK: Created bmlutils.h stubs: " + ", ".join(created))
else:
    print("OK: bmlutils.h stubs already present")

# Never exit non-zero. Real problems surface at compile time with a clear error.
print("DONE: minimal bmlutils patch applied")
