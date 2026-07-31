#
# Copyright (C) 2026 The Android Open Source Project
# Copyright (C) 2026 SebaUbuntu's TWRP device tree generator
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/vivo/PD2324

# For building with minimal manifest
ALLOW_MISSING_DEPENDENCIES := true
DISABLE_HOST_INIT_VERIFIER := true
BUILD_BROKEN_DUP_RULES := true
BUILD_BROKEN_ELF_PREBUILT_PRODUCT_COPY_FILES := true

# A/B
AB_OTA_UPDATER := true
AB_OTA_PARTITIONS += \
    boot \
    odm \
    vendor_dlkm \
    odm_dlkm \
    vendor_boot \
    system \
    vbmeta_vendor \
    system_ext \
    vendor \
    init_boot \
    vbmeta_system \
    product
BOARD_USES_RECOVERY_AS_BOOT := true

# Architecture
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_ABI2 := 
TARGET_CPU_VARIANT := generic
TARGET_CPU_VARIANT_RUNTIME := cortex-a55

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv7-a-neon
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic
TARGET_2ND_CPU_VARIANT_RUNTIME := cortex-a55

# APEX

# Bootloader
TARGET_BOOTLOADER_BOARD_NAME := mt6989
TARGET_NO_BOOTLOADER := true

# Display
TARGET_SCREEN_DENSITY := 480

# Kernel
BOARD_BOOTIMG_HEADER_VERSION := 4
BOARD_RAMDISK_USE_LZ4 := true
BOARD_KERNEL_CMDLINE := bootopt=64S3,32N2,64N2 product.solution=MTK
BOARD_KERNEL_PAGESIZE := 4096
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOTIMG_HEADER_VERSION)
BOARD_KERNEL_IMAGE_NAME := Image
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
TARGET_KERNEL_CONFIG := PD2324_defconfig
TARGET_KERNEL_SOURCE := kernel/vivo/PD2324

# Kernel - prebuilt
TARGET_FORCE_PREBUILT_KERNEL := true
ifeq ($(TARGET_FORCE_PREBUILT_KERNEL),true)
TARGET_PREBUILT_KERNEL := $(DEVICE_PATH)/prebuilt/kernel
TARGET_PREBUILT_DTB := $(DEVICE_PATH)/prebuilt/dtb.img
BOARD_MKBOOTIMG_ARGS += --dtb $(TARGET_PREBUILT_DTB)
BOARD_INCLUDE_DTB_IN_BOOTIMG := 
endif

# Partitions
BOARD_FLASH_BLOCK_SIZE := 262144 # (BOARD_KERNEL_PAGESIZE * 64)
BOARD_BOOTIMAGE_PARTITION_SIZE := 100663296
BOARD_HAS_LARGE_FILESYSTEM := true
BOARD_SYSTEMIMAGE_PARTITION_TYPE := ext4
BOARD_USERDATAIMAGE_FILE_SYSTEM_TYPE := f2fs
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
TARGET_COPY_OUT_VENDOR := vendor
BOARD_SUPER_PARTITION_SIZE := 9126805504 # TODO: Fix hardcoded value
BOARD_SUPER_PARTITION_GROUPS := vivo_dynamic_partitions
BOARD_VIVO_DYNAMIC_PARTITIONS_PARTITION_LIST := system system_ext vendor product odm vendor_dlkm odm_dlkm
BOARD_VIVO_DYNAMIC_PARTITIONS_SIZE := 9122611200 # TODO: Fix hardcoded value

# Platform
TARGET_BOARD_PLATFORM := mt6989

# Recovery
TARGET_RECOVERY_PIXEL_FORMAT := BGRA_8888
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true

# Encryption - disabled for initial bring-up (TW_INCLUDE_CRYPTO_FBE pulls
# keystore2 AIDL deps like android.security.apc that need frameworks/base
# fully built; deferred until boot is confirmed working)
# TW_INCLUDE_CRYPTO := true
# TW_INCLUDE_CRYPTO_FBE := true
# TW_INCLUDE_FBE_METADATA_DECRYPT := true
BOARD_USES_METADATA_PARTITION := true

# Recovery kernel modules (MTK UFS/MMC drivers are modules, not built-in)
# BOARD_RECOVERY_KERNEL_MODULES not used - modules loaded from vendor_boot via TW_LOAD_VENDOR_BOOT_MODULES
# BOARD_RECOVERY_KERNEL_MODULES := $(wildcard $(DEVICE_PATH)/recovery/root/lib/modules/*.ko)

# Load kernel modules at recovery boot time (UFS/MMC/display drivers
# are loadable modules on mt6989, not built-in). Without this, TWRP's
# KernelModuleLoader never loads them and init hangs waiting for
# /dev/block/* to appear, triggering AP watchdog reset (BR_WDT_BY_PASS_PWK).
TW_LOAD_VENDOR_BOOT_MODULES := true
TW_LOAD_VENDOR_MODULES_EXCLUDE_GKI := true
TW_LOAD_VENDOR_MODULES := "bootprof.ko nvmem_mtk-devinfo.ko mtk_wdt.ko timer-mediatek.ko device-apc-common.ko device-apc-mt6989.ko mtk-mbox-mailbox.ko tinysys-scmi.ko ise_lpm.ko mtk-ise-mailbox.ko pinctrl-mtk-v2.ko pinctrl-mt6989.ko iommu_debug.ko smmu_secure.ko arm_smmu_v3.ko mm-fake-engine.ko system_heap.ko mtk-scpsys.ko clk-common.ko clk-fmeter-mt6989.ko ise-trusty.ko ise-trusty-log.ko ise-trusty-ipc.ko ise-trusty-virtio.ko vcp_status.ko vcp.ko mtk-dvfsrc-regulator.ko mtk-emi.ko mtk-dvfsrc.ko mtk-hw-semaphore.ko clk-mt6989.ko clk-mt6989-peri.ko clk-mt6989-bus.ko clk-mt6989-vlp.ko mtk-pmic-wrap.ko mtk-spmi-pmic.ko spmi-mtk-pmif.ko mt6316-regulator.ko mt6363-regulator.ko mt6373-regulator.ko mt6681-regulator.ko mtk-vmm-spm-mt6989.ko mtk-scpsys-mt6989.ko mtk-scpsys-bringup.ko mt6989_dcm.ko mtk_dcm.ko clk-bringup.ko clk-chk-mt6989.ko mtk-dvfsrc-helper.ko mtk-dvfsrc-devfreq.ko mtk_dramc.ko mtk-smi.ko mtk-icc-core.ko mtk-cmdq-drv-ext.ko cmdq-platform-mt6989.ko cmdq_helper_inf.ko rt4831a_drv.ko mtk_panel_ext.ko vivo_display.ko panel_common.ko panel-nt37801-cmd-fhd.ko panel-nt37801-cmd-fhd-plus.ko drm_dma_helper.ko drm_display_helper.ko mediatek-drm.ko mtk_vdisp.ko mmprofile.ko mtk_dpc.ko mmqos-common.ko mmqos-mt6989.ko mtk-mmdvfs-v3.ko mtk-mmdvfs.ko cqhci.ko mtk-mmc-dbg.ko mtk-mmc.ko phy-mtk-ufs.ko rpmb.ko rpmb-mtk.ko ufs-mediatek-mod-ise.ko ufs-mediatek-dbg.ko blocktag.ko phy-mtk-xsphy.ko xhci-mtk-hcd-v2.ko mtu3.ko usb_boost.ko extcon-mtk-usb.ko i2c-mt65xx.ko spi-mt65xx.ko vivo_ts.ko mt6685-core.ko mt6685-nvtclk.ko mt6681-core.ko clkbuf.ko ffa_v10.ko teeperf.ko mcDrvModule-ffa.ko mtk-spmi-pmic-adc.ko pinctrl-mt6373.ko reboot-mode.ko syscon-reboot-mode.ko"

# Security patch level
PLATFORM_SECURITY_PATCH := 2099-12-31
PLATFORM_VERSION := 99.87.36
PLATFORM_VERSION_LAST_STABLE := $(PLATFORM_VERSION)
VENDOR_SECURITY_PATCH := 2099-12-31
BOOT_SECURITY_PATCH := 2099-12-31

# TWRP Configuration
TW_THEME := portrait_hdpi
TW_EXTRA_LANGUAGES := true
TW_SCREEN_BLANK_ON_BOOT := true
TW_INPUT_BLACKLIST := "hbtp_vm"
TW_USE_TOOLBOX := true
TW_INCLUDE_REPACKTOOLS := true
TW_EXCLUDE_APEX := true