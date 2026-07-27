#
# Copyright (C) 2026 The Android Open Source Project
# Copyright (C) 2026 SebaUbuntu's TWRP device tree generator
#
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from those products. Most specific first.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit some common TWRP stuff.
$(call inherit-product, vendor/twrp/config/common.mk)

# Inherit from PD2324 device
$(call inherit-product, device/vivo/PD2324/device.mk)

PRODUCT_DEVICE := PD2324
PRODUCT_NAME := twrp_PD2324
PRODUCT_BRAND := vivo
PRODUCT_MODEL := V2324A
PRODUCT_MANUFACTURER := vivo

PRODUCT_GMS_CLIENTID_BASE := android-vivo

PRODUCT_BUILD_PROP_OVERRIDES += \
    PRIVATE_BUILD_DESC="hal_mgvi_64_armv82-user 14 UP1A.231005.007 compiler260611211957 release-keys"

BUILD_FINGERPRINT := vivo/PD2324/PD2324:14/UP1A.231005.007/compiler260611211957:user/release-keys

# Recovery root files (init scripts)
# Use literal device/vivo/PD2324 path - $(DEVICE_PATH) is not available in product mk context
RECOVERY_ROOT_FILES := \
    device/vivo/PD2324/recovery/root/init.recovery.platform.rc:$(TARGET_COPY_OUT_RECOVERY)/root/init.recovery.platform.rc \
    device/vivo/PD2324/recovery/root/init.recovery.svc.rc:$(TARGET_COPY_OUT_RECOVERY)/root/init.recovery.svc.rc \
    device/vivo/PD2324/recovery/root/init.recovery.touch.rc:$(TARGET_COPY_OUT_RECOVERY)/root/init.recovery.touch.rc \
    device/vivo/PD2324/recovery/root/init.recovery.wifi.rc:$(TARGET_COPY_OUT_RECOVERY)/root/init.recovery.wifi.rc \
    device/vivo/PD2324/recovery/root/mtk-plpath-utils.rc:$(TARGET_COPY_OUT_RECOVERY)/root/mtk-plpath-utils.rc \
    device/vivo/PD2324/recovery/root/servicemanager.recovery.rc:$(TARGET_COPY_OUT_RECOVERY)/root/servicemanager.recovery.rc

PRODUCT_COPY_FILES += $(RECOVERY_ROOT_FILES)
