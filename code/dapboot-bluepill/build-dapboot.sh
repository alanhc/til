#!/bin/bash
# Build dapboot for the Blue Pill (runs in WSL / Linux).
# Uses an arm-none-eabi style GCC; here the old Zephyr SDK 0.10.3 toolchain,
# which has no newlib-nano, so nano.specs is commented out.
set -e
git clone https://github.com/devanlai/dapboot.git
cd dapboot
git checkout 8a1f099f6e43ce292eee3a326bd810b7e55f198f
git submodule update --init
cd src
sed -i 's/^LDFLAGS    += -specs=nano.specs/# &/' rules.mk
export PATH="$HOME/zephyr-sdk-0.10.3/arm-zephyr-eabi/bin:$PATH"
make TARGET=BLUEPILL PREFIX=arm-zephyr-eabi-
# With a normal Arm GNU Toolchain you can skip the sed and just run:
#   make TARGET=BLUEPILL
