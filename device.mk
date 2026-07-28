#
# Copyright (C) 2026 The Android Open Source Project
# Copyright (C) 2026 SebaUbuntu's TWRP device tree generator
#
# SPDX-License-Identifier: Apache-2.0
#

LOCAL_PATH := device/vivo/PD2324

# Dynamic partitions
PRODUCT_USE_DYNAMIC_PARTITIONS := true

# A/B
AB_OTA_POSTINSTALL_CONFIG +=     RUN_POSTINSTALL_system=true     POSTINSTALL_PATH_system=system/bin/otapreopt_script     FILESYSTEM_TYPE_system=ext4     POSTINSTALL_OPTIONAL_system=true

# A/B update packages (needed for update_engine_sideload)
PRODUCT_PACKAGES +=     otapreopt_script     update_engine_sideload
