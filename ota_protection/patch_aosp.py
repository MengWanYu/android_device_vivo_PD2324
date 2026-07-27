#!/usr/bin/env python3
"""Apply OTA partition protection + vivo/MTK stubs to AOSP bootable/recovery."""

import re, sys, os

RECOVERY_DIR = sys.argv[1] if len(sys.argv) > 1 else "bootable/recovery"

# ============================================================
# 1. Patch updater/install.cpp
# ============================================================
install_cpp = os.path.join(RECOVERY_DIR, "updater/install.cpp")
with open(install_cpp, 'r') as f:
    content = f.read()

# 1a. Add #include <set> after the last conditional include
content = content.replace(
    '#ifndef __ANDROID__\n#include <cutils/memory.h>  // for strlcpy\n#endif',
    '#ifndef __ANDROID__\n#include <cutils/memory.h>  // for strlcpy\n#endif\n\n#include <set>'
)

# 1b. Insert IsProtectedPath + WriteRawPlImageFn before "static bool UpdateBlockDeviceNameForPartition"
new_functions = '''static bool IsProtectedPath(const std::string& dest_path) {
  static const std::set<std::string> kProtectedPartitions = {
    "/dev/block/by-name/lk1",
    "/dev/block/by-name/lk2",
    "/dev/block/by-name/lk_a",
    "/dev/block/by-name/lk_b",
    "/dev/block/by-name/recovery",
    "/dev/block/mmcblk0boot0",
    "/dev/block/mmcblk0boot1",
  };

  for (const auto& part : kProtectedPartitions) {
    if (dest_path.find(part) != std::string::npos) {
      return true;
    }
  }
  return false;
}

// write_raw_pl_image(filename, partition)
// MTK-specific: writes preloader raw image to mmcblk0boot partition.
// Always blocked to prevent accidental bootloader overwrite via OTA.
Value* WriteRawPlImageFn(const char* name, State* state,
                         const std::vector<std::unique_ptr<Expr>>& argv) {
  if (argv.size() != 2) {
    return ErrorAbort(state, kArgsParsingFailure, "%s() expects 2 args, got %zu", name,
                      argv.size());
  }

  std::vector<std::string> args;
  if (!ReadArgs(state, argv, &args)) {
    return ErrorAbort(state, kArgsParsingFailure, "%s() Failed to parse %zu args", name,
                      argv.size());
  }

  const std::string& zip_path = args[0];
  std::string dest_path = args[1];

  state->updater->UiPrint(android::base::StringPrintf(
      "[PROTECTED] write_raw_pl_image(%%s, %%s) -- skipped (bootloader/preloader protected)",
      zip_path.c_str(), dest_path.c_str()));
  return StringValue("t");
}

'''

content = content.replace(
    'static bool UpdateBlockDeviceNameForPartition(UpdaterInterface* updater, Partition* partition) {',
    new_functions + 'static bool UpdateBlockDeviceNameForPartition(UpdaterInterface* updater, Partition* partition) {'
)

# 1c. Insert IsProtectedPath check in PackageExtractFileFn (2-arg version)
# After FindBlockDeviceName resolves the dest_path, before open()
old_block = '''    if (std::string block_device_name = state->updater->FindBlockDeviceName(dest_path);
        !block_device_name.empty()) {
      dest_path = block_device_name;
    }

    android::base::unique_fd fd(TEMP_FAILURE_RETRY(
        open(dest_path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR)));'''

new_block = '''    if (std::string block_device_name = state->updater->FindBlockDeviceName(dest_path);
        !block_device_name.empty()) {
      dest_path = block_device_name;
    }

    if (IsProtectedPath(dest_path)) {
      state->updater->UiPrint(android::base::StringPrintf(
          "[PROTECTED] package_extract_file(%%s, %%s) -- skipped (partition protected)",
          zip_path.c_str(), dest_path.c_str()));
      return StringValue("t");
    }

    android::base::unique_fd fd(TEMP_FAILURE_RETRY(
        open(dest_path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR)));'''

if old_block in content:
    content = content.replace(old_block, new_block)
else:
    print("WARNING: Could not find PackageExtractFileFn anchor #1, trying fuzzy match...")
    # Try fuzzy match - just find the FindBlockDeviceName call
    if 'FindBlockDeviceName(dest_path)' in content:
        print("  Found FindBlockDeviceName call, attempting insertion...")
        # Use a different anchor
        alt_old = '''    if (std::string block_device_name = state->updater->FindBlockDeviceName(dest_path);
        !block_device_name.empty()) {
      dest_path = block_device_name;
    }'''
        if alt_old in content:
            content = content.replace(alt_old, alt_old + '''

    if (IsProtectedPath(dest_path)) {
      state->updater->UiPrint(android::base::StringPrintf(
          "[PROTECTED] package_extract_file(%%s, %%s) -- skipped (partition protected)",
          zip_path.c_str(), dest_path.c_str()));
      return StringValue("t");
    }''')
            print("  Fuzzy insert succeeded.")
        else:
            print("  ERROR: Could not find anchor for IsProtectedPath insertion!")
    else:
        print("  ERROR: FindBlockDeviceName not found in install.cpp!")

# 1d. Insert make_parents before "// rename(src_name, dst_name)"
make_parents_code = '''static bool make_parents(const std::string& path) {
  size_t pos = 0;
  while ((pos = path.find('/', pos + 1)) != std::string::npos) {
    std::string dir = path.substr(0, pos);
    if (mkdir(dir.c_str(), 0755) != 0 && errno != EEXIST) {
      return false;
    }
  }
  return true;
}

'''

old_rename_comment = '// rename(src_name, dst_name)'
if old_rename_comment in content:
    content = content.replace(old_rename_comment, make_parents_code + old_rename_comment)
else:
    print("WARNING: Could not find rename comment anchor for make_parents insertion")

# 1e. Insert vivo/MTK stubs before RegisterInstallFunctions
vivo_stubs = '''// --- vivo/MTK OTA compatibility stubs ---

// switch_active(part1, part2) - MTK dual-slot switch
// No-op: slot switching is dangerous and unnecessary for TWRP OTA
Value* SwitchActiveFn(const char* name, State* state, const std::vector<std::unique_ptr<Expr>>& argv) {
  if (argv.size() != 2) {
    return ErrorAbort(state, kArgsParsingFailure, "%s() expects 2 args, got %zu", name, argv.size());
  }

  std::vector<std::string> args;
  if (!ReadArgs(state, argv, &args)) {
    return ErrorAbort(state, kArgsParsingFailure, "%s(): Failed to parse the argument(s)", name);
  }

  state->updater->UiPrint(android::base::StringPrintf(
      "[TWRP] switch_active(%%s, %%s) -- no-op (slot switching disabled)",
      args[0].c_str(), args[1].c_str()));
  return StringValue("t");
}

// set_mtupdate_stage(path, stage) - MTK update stage tracking
Value* SetMtUpdateStageFn(const char* name, State* state, const std::vector<std::unique_ptr<Expr>>& argv) {
  if (argv.size() != 2) {
    return ErrorAbort(state, kArgsParsingFailure, "%s() expects 2 args, got %zu", name, argv.size());
  }

  std::vector<std::string> args;
  if (!ReadArgs(state, argv, &args)) {
    return ErrorAbort(state, kArgsParsingFailure, "%s(): Failed to parse the argument(s)", name);
  }

  auto updater_runtime = state->updater->GetRuntime();
  if (!updater_runtime->WriteStringToFile(args[1], args[0])) {
    PLOG(ERROR) << name << ": Failed to write stage to " << args[0];
    return StringValue("");
  }
  return StringValue("t");
}

// get_mtupdate_stage(path) - MTK update stage query
Value* GetMtUpdateStageFn(const char* name, State* state, const std::vector<std::unique_ptr<Expr>>& argv) {
  if (argv.size() != 1) {
    return ErrorAbort(state, kArgsParsingFailure, "%s() expects 1 arg, got %zu", name, argv.size());
  }

  std::vector<std::string> args;
  if (!ReadArgs(state, argv, &args)) {
    return ErrorAbort(state, kArgsParsingFailure, "%s(): Failed to parse the argument(s)", name);
  }

  std::string contents;
  auto updater_runtime = state->updater->GetRuntime();
  if (updater_runtime->ReadFileToString(args[0], &contents)) {
    contents.erase(contents.find_last_not_of(" \\t\\n\\r") + 1);
    return StringValue(contents);
  }

  return StringValue("0");
}

// show_mtupdate_stage(path) - Display MTK update stage
Value* ShowMtUpdateStageFn(const char* name, State* state, const std::vector<std::unique_ptr<Expr>>& argv) {
  if (argv.size() != 1) {
    return ErrorAbort(state, kArgsParsingFailure, "%s() expects 1 arg, got %zu", name, argv.size());
  }

  std::vector<std::string> args;
  if (!ReadArgs(state, argv, &args)) {
    return ErrorAbort(state, kArgsParsingFailure, "%s(): Failed to parse the argument(s)", name);
  }

  std::string contents;
  auto updater_runtime = state->updater->GetRuntime();
  if (updater_runtime->ReadFileToString(args[0], &contents)) {
    contents.erase(contents.find_last_not_of(" \\t\\n\\r") + 1);
    state->updater->UiPrint(android::base::StringPrintf("MTK update stage: %%s", contents.c_str()));
  } else {
    state->updater->UiPrint("MTK update stage: 0 (not started)");
  }
  return StringValue("t");
}

// update_sleep(seconds) - vivo OTA sleep/wait
Value* UpdateSleepFn(const char* name, State* state, const std::vector<std::unique_ptr<Expr>>& argv) {
  if (argv.size() != 1) {
    return ErrorAbort(state, kArgsParsingFailure, "%s() expects 1 arg, got %zu", name, argv.size());
  }

  std::vector<std::string> args;
  if (!ReadArgs(state, argv, &args)) {
    return ErrorAbort(state, kArgsParsingFailure, "%s(): Failed to parse the argument(s)", name);
  }

  int seconds;
  if (!android::base::ParseInt(args[0], &seconds)) {
    return ErrorAbort(state, kArgsParsingFailure, "%s(): Failed to parse seconds from \\"%s\\"", name, args[0].c_str());
  }

  state->updater->UiPrint(android::base::StringPrintf("update_sleep(%%s)...", args[0].c_str()));
  sleep(seconds);
  return StringValue("t");
}

// file_image_resize_cow(type, path, flag) - vivo COW/DYN partition resize
// No-op: COW partition management is a vivo OTA internal detail
Value* FileImageResizeCowFn(const char* name, State* state, const std::vector<std::unique_ptr<Expr>>& argv) {
  if (argv.size() != 3) {
    return ErrorAbort(state, kArgsParsingFailure, "%s() expects 3 args, got %zu", name, argv.size());
  }

  std::vector<std::string> args;
  if (!ReadArgs(state, argv, &args)) {
    return ErrorAbort(state, kArgsParsingFailure, "%s(): Failed to parse the argument(s)", name);
  }

  state->updater->UiPrint(android::base::StringPrintf(
      "[TWRP] file_image_resize_cow(%%s, %%s, %%s) -- no-op",
      args[0].c_str(), args[1].c_str(), args[2].c_str()));
  return StringValue("t");
}

// post_ota_action() - vivo post-OTA cleanup
// No-op: TWRP handles post-install cleanup independently
Value* PostOtaActionFn(const char* name, State* state, const std::vector<std::unique_ptr<Expr>>& argv __attribute__((unused))) {
  if (argv.size() != 0) {
    return ErrorAbort(state, kArgsParsingFailure, "%s() expects 0 args, got %zu", name, argv.size());
  }

  state->updater->UiPrint("[TWRP] post_ota_action() -- no-op");
  return StringValue("t");
}

'''

if 'void RegisterInstallFunctions() {' in content:
    content = content.replace(
        'void RegisterInstallFunctions() {',
        vivo_stubs + 'void RegisterInstallFunctions() {'
    )
else:
    print("ERROR: Could not find RegisterInstallFunctions!")

# 1f. Add vivo/MTK function registrations at the end of RegisterInstallFunctions
# Find the last RegisterFunction call before the closing }
old_last_reg = '  RegisterFunction("add_slot_suffix", AddSlotSuffixFn);'
new_last_reg = '''  RegisterFunction("add_slot_suffix", AddSlotSuffixFn);

  // vivo/MTK OTA compatibility
  RegisterFunction("switch_active", SwitchActiveFn);
  RegisterFunction("set_mtupdate_stage", SetMtUpdateStageFn);
  RegisterFunction("get_mtupdate_stage", GetMtUpdateStageFn);
  RegisterFunction("show_mtupdate_stage", ShowMtUpdateStageFn);
  RegisterFunction("update_sleep", UpdateSleepFn);
  RegisterFunction("file_image_resize_cow", FileImageResizeCowFn);
  RegisterFunction("post_ota_action", PostOtaActionFn);'''

if old_last_reg in content:
    content = content.replace(old_last_reg, new_last_reg)
else:
    # Try to find any last RegisterFunction before closing brace
    print("WARNING: Could not find add_slot_suffix registration, trying pattern match...")
    # Find the last RegisterFunction line before the closing }
    match = re.search(r'(  RegisterFunction\("[^"]+", [^;]+\);)\n\}', content)
    if match:
        content = content.replace(
            match.group(0),
            match.group(1) + '\n\n  // vivo/MTK OTA compatibility\n'
            '  RegisterFunction("write_raw_pl_image", WriteRawPlImageFn);\n'
            '  RegisterFunction("switch_active", SwitchActiveFn);\n'
            '  RegisterFunction("set_mtupdate_stage", SetMtUpdateStageFn);\n'
            '  RegisterFunction("get_mtupdate_stage", GetMtUpdateStageFn);\n'
            '  RegisterFunction("show_mtupdate_stage", ShowMtUpdateStageFn);\n'
            '  RegisterFunction("update_sleep", UpdateSleepFn);\n'
            '  RegisterFunction("file_image_resize_cow", FileImageResizeCowFn);\n'
            '  RegisterFunction("post_ota_action", PostOtaActionFn);\n}'
        )
        print("  Pattern match succeeded!")
    else:
        print("ERROR: Could not find insertion point for function registrations!")

# Also register write_raw_pl_image alongside other partition functions
old_mount_reg = '  RegisterFunction("package_extract_file", PackageExtractFileFn);'
new_mount_reg = '''  RegisterFunction("package_extract_file", PackageExtractFileFn);
  RegisterFunction("write_raw_pl_image", WriteRawPlImageFn);'''

if old_mount_reg in content:
    content = content.replace(old_mount_reg, new_mount_reg)
else:
    print("WARNING: Could not find package_extract_file registration for write_raw_pl_image!")

# Also ensure StringPrintf include is present for UiPrint
if '#include <android-base/stringprintf.h>' not in content:
    content = content.replace(
        '#include <android-base/strings.h>',
        '#include <android-base/strings.h>\n#include <android-base/stringprintf.h>'
    )

with open(install_cpp, 'w') as f:
    f.write(content)
print("✅ Patched updater/install.cpp")

# ============================================================
# 2. Patch updater/Android.mk - add include path for bmlutils
# ============================================================
android_mk = os.path.join(RECOVERY_DIR, "updater/Android.mk")
with open(android_mk, 'r') as f:
    mk_content = f.read()

# Add LOCAL_C_INCLUDES for bmlutils (after existing LOCAL_C_INCLUDES if any)
bmlutils_include = '\n# OTA protection: add bootable/recovery to include path for bmlutils\nLOCAL_C_INCLUDES += $(LOCAL_PATH)/..\n'

if 'LOCAL_C_INCLUDES += $(LOCAL_PATH)/..' not in mk_content:
    # Insert before LOCAL_MODULE or LOCAL_STATIC_LIBRARIES or at end
    if 'LOCAL_MODULE :=' in mk_content:
        mk_content = mk_content.replace(
            'LOCAL_MODULE :=',
            bmlutils_include + 'LOCAL_MODULE :='
        )
    elif 'include $(BUILD_EXECUTABLE)' in mk_content:
        mk_content = mk_content.replace(
            'include $(BUILD_EXECUTABLE)',
            bmlutils_include + 'include $(BUILD_EXECUTABLE)'
        )
    else:
        mk_content += bmlutils_include

with open(android_mk, 'w') as f:
    f.write(mk_content)
print("✅ Patched updater/Android.mk")

# ============================================================
# 3. Patch applypatch/Android.bp - add include_dirs for bmlutils
# ============================================================
android_bp = os.path.join(RECOVERY_DIR, "applypatch/Android.bp")
with open(android_bp, 'r') as f:
    bp_content = f.read()

if '"bootable/recovery"' not in bp_content and 'include_dirs: ["bootable/recovery"]' not in bp_content:
    # Add include_dirs before the closing of the module definition
    # Find a good insertion point - after srcs or name
    if 'include_dirs:' in bp_content:
        # Already has include_dirs, append to it
        bp_content = bp_content.replace(
            'include_dirs: [',
            'include_dirs: ["bootable/recovery", '
        )
    else:
        # Add include_dirs after srcs line
        bp_content = re.sub(
            r'(srcs: \[[^\]]+\])',
            r'\1\n    include_dirs: ["bootable/recovery"],',
            bp_content
        )

with open(android_bp, 'w') as f:
    f.write(bp_content)
print("✅ Patched applypatch/Android.bp")

# ============================================================
# Verification
# ============================================================
with open(install_cpp, 'r') as f:
    verify = f.read()

checks = [
    ('PROTECTED', 'IsProtectedPath block'),
    ('WriteRawPlImageFn', 'WriteRawPlImageFn'),
    ('write_raw_pl_image', 'write_raw_pl_image registration'),
    ('SwitchActiveFn', 'vivo: switch_active'),
    ('SetMtUpdateStageFn', 'vivo: set_mtupdate_stage'),
    ('GetMtUpdateStageFn', 'vivo: get_mtupdate_stage'),
    ('ShowMtUpdateStageFn', 'vivo: show_mtupdate_stage'),
    ('UpdateSleepFn', 'vivo: update_sleep'),
    ('FileImageResizeCowFn', 'vivo: file_image_resize_cow'),
    ('PostOtaActionFn', 'vivo: post_ota_action'),
    ('make_parents', 'make_parents helper'),
]

all_ok = True
for text, desc in checks:
    if text in verify:
        print(f"  ✅ {desc}")
    else:
        print(f"  ❌ MISSING: {desc}")
        all_ok = False

if all_ok:
    print("✅ All OTA protection patches applied successfully!")
else:
    print("⚠️  Some patches may have failed - check the build log")
    sys.exit(1)
