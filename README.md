# Fairagotchi

Run Pwnagotchi on a Fairphone 3 using a custom Linux setup

This project aims to turn the Fairphone 3 into a fully standalone Pwnagotchi device with modem, GPS, and external Wi-Fi support.

For device-specific information see the official postmarketOS wiki page:

https://wiki.postmarketos.org/wiki/Fairphone_3_(fairphone-fp3)



---

# Current Status

| Component | Status |
|-----------|--------|
| Modem / WWAN | ✅ Working |
| GPS | ✅ Working *(SIM card required)* |
| Internal Wi-Fi Monitor Mode | ❌ Not working |
| Battery Indicator | ❌ Not working |
| USB-OTG External Wi-Fi | ✅ Working |

---

# Overview

Fairagotchi runs:

- Mainline-based Linux kernel for msm8953
- Custom initramfs
- Pwnagotchi userspace
- External USB Wi-Fi adapter in monitor mode
- Mobile data connection via internal modem

The goal is to create a fully portable pentesting platform powered by a smartphone.

---

# Building

## Requirements

You need:

- Standard Linux kernel build environment
- gcc-aarch64
- make
- bc
- flex
- bison
- openssl
- libssl-dev
- device-tree-compiler
- lz4
- cpio
- git

Additionally:

## make_ext4fs (required for sparse images)

Install from:

https://github.com/iglunix/make_ext4fs

This tool is required to generate Android-style sparse ext4 images.

---

## Build Process

Run:

```bash
./mk.sh

