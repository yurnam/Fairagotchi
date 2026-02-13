#!/bin/sh
fastboot flash boot images/boot.img
fastboot flash system_a images/modules.img
fastboot flash system_b images/firmware.img


