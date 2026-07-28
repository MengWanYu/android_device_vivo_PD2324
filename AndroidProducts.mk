#
# Copyright (C) 2026 The Android Open Source Project
# Copyright (C) 2026 SebaUbuntu's TWRP device tree generator
#
# SPDX-License-Identifier: Apache-2.0
#

PRODUCT_MAKEFILES := \
    $(LOCAL_DIR)/omni_PD2324.mk \
    $(LOCAL_DIR)/twrp_PD2324.mk

COMMON_LUNCH_CHOICES := \
    twrp_PD2324-trunk-eng \
    twrp_PD2324-trunk-userdebug