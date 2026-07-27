#!/usr/bin/env python3
"""Minimal patch: fix bmlutils build error only.

applypatch.cpp includes "bmlutils/bmlutils.h" which doesn't exist in the AOSP
bootable/recovery tree. We add include_dirs: ["bootable/recovery"] to the
applypatch Android.bp so the include resolves to bootable/recovery/bmlutils/
if present, and more importantly so the module finds its sibling headers.

OTA partition protection is intentionally NOT applied here (kept out of scope
for now). This script only fixes the compilation error.
"""

import re
import sys
import os

RECOVERY_DIR = sys.argv[1] if len(sys.argv) > 1 else "bootable/recovery"

# ============================================================
# Patch applypatch/Android.bp - add include_dirs for bmlutils
# ============================================================
android_bp = os.path.join(RECOVERY_DIR, "applypatch/Android.bp")
with open(android_bp, 'r') as f:
    bp_content = f.read()

patched = False
if 'include_dirs: ["bootable/recovery"]' not in bp_content:
    if 'include_dirs:' in bp_content:
        # Already has include_dirs, prepend bootable/recovery
        bp_content = bp_content.replace(
            'include_dirs: [',
            'include_dirs: ["bootable/recovery", ',
            1
        )
        patched = True
    else:
        # Add include_dirs after the first srcs block
        new_bp = re.sub(
            r'(srcs: \[[^\]]*\],)',
            r'\1\n    include_dirs: ["bootable/recovery"],',
            bp_content,
            count=1
        )
        if new_bp != bp_content:
            bp_content = new_bp
            patched = True

    if patched:
        with open(android_bp, 'w') as f:
            f.write(bp_content)
        print("OK: Patched applypatch/Android.bp (added include_dirs for bmlutils)")
    else:
        print("WARNING: could not find insertion point in applypatch/Android.bp")
else:
    print("OK: applypatch/Android.bp already has include_dirs, nothing to do")

# ============================================================
# Also fix updater/Android.mk include path (harmless, helps bmlutils resolve)
# ============================================================
android_mk = os.path.join(RECOVERY_DIR, "updater/Android.mk")
if os.path.isfile(android_mk):
    with open(android_mk, 'r') as f:
        mk_content = f.read()
    marker = 'LOCAL_C_INCLUDES += $(LOCAL_PATH)/..'
    if marker not in mk_content:
        add = '\n# bmlutils include path fix\n' + marker + '\n'
        if 'LOCAL_MODULE :=' in mk_content:
            mk_content = mk_content.replace('LOCAL_MODULE :=', add + 'LOCAL_MODULE :=', 1)
        elif 'include $(BUILD_EXECUTABLE)' in mk_content:
            mk_content = mk_content.replace('include $(BUILD_EXECUTABLE)', add + 'include $(BUILD_EXECUTABLE)', 1)
        else:
            mk_content += add
        with open(android_mk, 'w') as f:
            f.write(mk_content)
        print("OK: Patched updater/Android.mk (include path)")

# ============================================================
# Create empty bmlutils/bmlutils.h stub (belt-and-suspenders)
# applypatch.cpp just #includes it; an empty header satisfies the compiler
# since applypatch doesn't actually call any bmlutils symbol.
# ============================================================
bmlutils_dir = os.path.join(RECOVERY_DIR, "bmlutils")
bmlutils_h = os.path.join(bmlutils_dir, "bmlutils.h")
if not os.path.isfile(bmlutils_h):
    os.makedirs(bmlutils_dir, exist_ok=True)
    stub = (
        "#ifndef BMLUTILS_H_\n"
        "#define BMLUTILS_H_\n"
        "/* Empty stub: bmlutils not present. applypatch only #includes it. */\n"
        "#endif  // BMLUTILS_H_\n"
    )
    with open(bmlutils_h, 'w') as f:
        f.write(stub)
    print("OK: Created bmlutils/bmlutils.h empty stub")

# Never exit non-zero: this is a best-effort build fix.
# A missing patch should fail later at compile time with a clear error,
# not silently abort the whole workflow here.
print("DONE: minimal bmlutils patch applied")
