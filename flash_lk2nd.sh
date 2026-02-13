#!/bin/sh

fastboot flash boot_a resources/lk2nd.img
fastboot flash boot_b resources/lk2nd.img
fastboot flash dtbo_a resources/dtbo.img
fastboot flash dtbo_b resources/dtbo.img
