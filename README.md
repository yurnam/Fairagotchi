# Fairagotchi

Run Pwnagotchi on a Fairphone 3 using a custom Linux setup.

This project turns the Fairphone 3 into a fully standalone Pwnagotchi device with modem, GPS, and external Wi-Fi support. It can also be used to boot any ARM64 Linux rootfs on a Fairphone 3.

For device-specific information see the official postmarketOS wiki page:
https://wiki.postmarketos.org/wiki/Fairphone_3_(fairphone-fp3)

---

## Table of Contents

- [Current Status](#current-status)
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Building](#building)
- [Preparing the Pwnagotchi Rootfs](#preparing-the-pwnagotchi-rootfs)
- [Flashing to Fairphone 3](#flashing-to-fairphone-3)
- [Post-Installation Configuration](#post-installation-configuration)
- [Using with Other ARM64 Linux Distributions](#using-with-other-arm64-linux-distributions)
- [Troubleshooting](#troubleshooting)

---

## Current Status

| Component | Status |
|-----------|--------|
| Modem / WWAN | ✅ Working |
| GPS | ✅ Working *(SIM card required)* |
| Internal Wi-Fi Monitor Mode | ❌ Not working |
| Battery Indicator | ❌ Not working |
| USB-OTG External Wi-Fi | ✅ Working |

---

## Overview

Fairagotchi runs:

- Mainline-based Linux kernel (6.17.7) for msm8953/sdm632
- Custom initramfs with Android boot image format
- Pwnagotchi userspace on top of Raspberry Pi image
- External USB Wi-Fi adapter in monitor mode (required for packet capture)
- Mobile data connection via internal modem (optional)
- GPS via Qualcomm modem (requires SIM card)

The goal is to create a fully portable pentesting platform powered by a smartphone.

---

## Prerequisites

### Hardware Requirements

- **Fairphone 3** (or Fairphone 3+)
- **USB-OTG cable** and **USB Wi-Fi adapter** with monitor mode support (e.g., ALFA AWUS036ACH, TP-Link TL-WN722N v1)
- **microSD card** (16GB minimum) with Pwnagotchi Raspberry Pi image
- **USB cable** for fastboot connection to computer
- **SIM card** (optional, required for GPS functionality)

### Software Requirements

#### On Your Build Machine (Linux)

Install the following packages:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    gcc-aarch64-linux-gnu \
    make \
    bc \
    flex \
    bison \
    libssl-dev \
    device-tree-compiler \
    lz4 \
    cpio \
    git \
    android-sdk-platform-tools
```

**Arch Linux:**
```bash
sudo pacman -S base-devel aarch64-linux-gnu-gcc make bc flex bison openssl dtc lz4 cpio git android-tools
```

#### make_ext4fs Tool

This tool is required to generate Android-style sparse ext4 images.

```bash
# Clone and build make_ext4fs
git clone https://github.com/iglunix/make_ext4fs.git
cd make_ext4fs
make
sudo make install
cd ..
```

---

## Building

### 1. Clone the Repository

```bash
git clone https://github.com/yurnam/Fairagotchi.git
cd Fairagotchi
```

### 2. Build Kernel and Images

Run the build script:

```bash
./mk.sh
```

This script will:
- Configure and compile the Linux kernel (6.17.7) for ARM64 with the Fairphone 3 device tree
- Build kernel modules
- Create a boot image (`images/boot.img`) with kernel and initramfs
- Create a modules image (`images/modules.img`) containing kernel modules
- Create a firmware image (`images/firmware.img`) with Qualcomm firmware files

The build process may take 15-45 minutes depending on your system.

### 3. Verify Build Output

After the build completes, verify that the images were created:

```bash
ls -lh images/
```

You should see:
- `boot.img` - Boot image with kernel and initramfs
- `modules.img` - Kernel modules (sparse ext4 image)
- `firmware.img` - Firmware files for modem, Wi-Fi, etc. (sparse ext4 image)

---

## Preparing the Pwnagotchi Rootfs

The userdata partition on your Fairphone 3 will hold the Pwnagotchi root filesystem from a Raspberry Pi SD card image.

### Option 1: Using a Standard Pwnagotchi Raspberry Pi SD Card Image (Recommended)

1. **Download Pwnagotchi Image**
   
   Download the latest Pwnagotchi Raspberry Pi image from:
   - Official releases: https://github.com/evilsocket/pwnagotchi/releases
   - Or use a custom build with your preferred configuration

2. **Extract the Root Filesystem**

   ```bash
   # Download the image (example)
   wget https://github.com/evilsocket/pwnagotchi/releases/download/v1.5.5/pwnagotchi-raspios-lite-v1.5.5.img.zip
   unzip pwnagotchi-raspios-lite-v1.5.5.img.zip
   
   # Mount the image to extract the rootfs
   # Find the rootfs partition offset
   fdisk -l pwnagotchi-raspios-lite-v1.5.5.img
   
   # Mount the second partition (rootfs) - adjust offset as needed
   # Typically starts at sector 532480, with 512 byte sectors = 272629760 bytes
   mkdir -p /tmp/pwnagotchi-rootfs
   sudo mount -o loop,offset=272629760 pwnagotchi-raspios-lite-v1.5.5.img /tmp/pwnagotchi-rootfs
   ```

3. **Install Custom Plugins and Scripts**

   Copy the Fairagotchi-specific files to the rootfs:

   ```bash
   # Copy display plugin (replaces the original)
   sudo cp plugins/display.py /tmp/pwnagotchi-rootfs/usr/local/lib/python3.9/dist-packages/pwnagotchi/plugins/default/display.py
   
   # Copy helper scripts
   sudo cp scripts/png2fb0.py /tmp/pwnagotchi-rootfs/usr/local/bin/
   sudo cp scripts/mmcli-gps-tty.py /tmp/pwnagotchi-rootfs/usr/local/sbin/
   sudo cp scripts/qmi-provision.sh /tmp/pwnagotchi-rootfs/usr/local/sbin/
   sudo chmod +x /tmp/pwnagotchi-rootfs/usr/local/bin/png2fb0.py
   sudo chmod +x /tmp/pwnagotchi-rootfs/usr/local/sbin/mmcli-gps-tty.py
   sudo chmod +x /tmp/pwnagotchi-rootfs/usr/local/sbin/qmi-provision.sh
   
   # Copy systemd services
   sudo cp systemd-services/*.service /tmp/pwnagotchi-rootfs/etc/systemd/system/
   
   # Enable services
   sudo chroot /tmp/pwnagotchi-rootfs /bin/bash -c "systemctl enable display-updater.service gps-qcom.service modem-up.service"
   ```

4. **Install Additional Dependencies**

   ```bash
   # Install ModemManager and GPS tools
   sudo chroot /tmp/pwnagotchi-rootfs /bin/bash -c "apt-get update && apt-get install -y modemmanager libqmi-utils python3-pil"
   ```

5. **Configure Pwnagotchi for External Wi-Fi**

   Edit the Pwnagotchi configuration to use your USB Wi-Fi adapter:

   ```bash
   sudo nano /tmp/pwnagotchi-rootfs/etc/pwnagotchi/config.toml
   ```

   Update the interface name to match your USB adapter (usually `wlan1`):
   ```toml
   main.iface = "wlan1"
   ```

6. **Unmount and Create the Userdata Image**

   ```bash
   sudo umount /tmp/pwnagotchi-rootfs
   
   # Create a sparse ext4 image from the rootfs directory
   # Note: This step is optional if you flash directly to the phone
   # You can also dd the rootfs partition directly to /dev/block/mmcblk0p62 when booted from TWRP
   ```

### Option 2: Quick Test with Minimal ARM64 Rootfs

For testing purposes, you can use any ARM64 Linux distribution:

```bash
# Example: Download Alpine Linux ARM64 rootfs
wget https://dl-cdn.alpinelinux.org/alpine/v3.18/releases/aarch64/alpine-minirootfs-3.18.0-aarch64.tar.gz

# Extract to a directory
mkdir -p rootfs
sudo tar -xzf alpine-minirootfs-3.18.0-aarch64.tar.gz -C rootfs/

# The build script will use this rootfs directory automatically
```

---

## Flashing to Fairphone 3

### Prerequisites

1. **Unlock Bootloader**
   
   Follow the official Fairphone guide:
   https://support.fairphone.com/hc/en-us/articles/360048646311

2. **Install TWRP Recovery** (Optional but recommended)
   
   TWRP is useful for backing up, restoring, and managing partitions:
   
   ```bash
   # Boot into fastboot mode (power off, hold Vol Down + Power)
   fastboot boot resources/twrp.img
   ```

3. **Boot into Fastboot Mode**
   
   Power off the phone, then hold **Volume Down + Power** until you see the fastboot screen.

### Flashing Process

#### Step 1: Flash LK2ND Bootloader (One-time setup)

LK2ND is a secondary bootloader that allows booting mainline Linux kernels:

```bash
./flash_lk2nd.sh
```

Or manually:
```bash
fastboot flash boot_a resources/lk2nd.img
fastboot flash boot_b resources/lk2nd.img
```

Reboot the phone. You should now see the LK2ND boot menu.

#### Step 2: Flash Fairagotchi Images

```bash
./flash.sh
```

Or manually:
```bash
fastboot flash boot images/boot.img
fastboot flash system_a images/modules.img
fastboot flash system_b images/firmware.img
fastboot flash dtbo_a resources/dtbo.img
fastboot flash dtbo_b resources/dtbo.img
```

**Partition Layout:**
- `boot` - Contains the kernel and initramfs
- `system_a` - Repurposed to hold kernel modules (mounted at `/lib/modules`)
- `system_b` - Repurposed to hold firmware files (mounted at `/lib/firmware`)
- `dtbo_a/dtbo_b` - Device tree overlays
- `userdata` - Root filesystem (Pwnagotchi or other ARM64 Linux)

#### Step 3: Flash the Rootfs to Userdata

You have several options:

**Option A: Using TWRP (Recommended)**

1. Boot into TWRP:
   ```bash
   fastboot boot resources/twrp.img
   ```

2. In TWRP, go to Wipe > Advanced > Select "Data" > Format Data

3. Use ADB to push the rootfs:
   ```bash
   # Mount userdata partition
   adb shell mount /dev/block/mmcblk0p62 /data
   
   # Push the rootfs tarball
   adb push pwnagotchi-rootfs.tar.gz /data/
   
   # Extract it
   adb shell "cd /data && tar -xzf pwnagotchi-rootfs.tar.gz && rm pwnagotchi-rootfs.tar.gz"
   ```

**Option B: Using dd from Linux (if booted into working system)**

```bash
# Create ext4 filesystem
mkfs.ext4 /dev/block/mmcblk0p62

# Mount and extract
mount /dev/block/mmcblk0p62 /mnt
tar -xzf /path/to/pwnagotchi-rootfs.tar.gz -C /mnt
umount /mnt
```

#### Step 4: Reboot

```bash
fastboot reboot
```

The phone should boot into the Fairagotchi system and start Pwnagotchi!

---

## Post-Installation Configuration

### Accessing the Device

1. **Via USB Network**
   
   Connect the phone via USB. It should appear as a USB ethernet device:
   
   ```bash
   ssh pi@10.0.0.2
   # Default password: raspberry
   ```

2. **Via Serial Console** (if USB networking doesn't work)
   
   You may need a USB serial adapter connected to the phone's debugging pins.

### Configure Mobile Data (Optional)

If you want to use the internal modem for internet connectivity:

1. Insert a SIM card
2. The `modem-up.service` should automatically provision the modem
3. Use ModemManager to configure APN:
   ```bash
   mmcli -m 0 --simple-connect="apn=your-apn-here"
   ```

### Configure GPS (Optional)

GPS requires a SIM card to be inserted (due to Qualcomm firmware requirements).

1. The `gps-qcom.service` exposes GPS as `/dev/ttyUSB9`
2. Configure Pwnagotchi to use this GPS device in `/etc/pwnagotchi/config.toml`

### Configure External USB Wi-Fi Adapter

1. Plug in your USB Wi-Fi adapter via OTG cable
2. Verify it's detected:
   ```bash
   ip link show
   # Should show wlan1 or similar
   ```
3. Ensure Pwnagotchi is configured to use the correct interface (`wlan1`)

### Display Updates

The custom `display.py` plugin exports PNG frames to `/var/tmp/pwnagotchi.png`.
The `png2fb0.py` script (run by `display-updater.service`) continuously pushes these frames to the phone's framebuffer (`/dev/fb0`).

---

## Using with Other ARM64 Linux Distributions

This project isn't limited to Pwnagotchi! You can use it to boot any ARM64 Linux distribution on the Fairphone 3.

### Supported Distributions

- **PostmarketOS** - Alpine-based mobile Linux
- **Mobian** - Debian for mobile devices
- **Ubuntu Touch**
- **Arch Linux ARM**
- **Alpine Linux**
- **Debian ARM64**
- Any other ARM64 rootfs

### Steps

1. **Build the kernel and images** as described above
2. **Flash the boot images** (boot, modules, firmware) using the same process
3. **Prepare your chosen rootfs:**
   - Download or build the ARM64 rootfs for your distribution
   - Extract to a directory or create an ext4 image
4. **Flash the rootfs to userdata** using TWRP or dd
5. **Configure init system:**
   - Ensure the init system expects to start from `/dev/mmcblk0p62`
   - The initramfs will mount this as root
6. **Reboot** and enjoy your chosen Linux distribution!

### Example: PostmarketOS

```bash
# Download PostmarketOS rootfs
wget https://images.postmarketos.org/...

# Flash as described above
# Configure device-specific files (display, modem, etc.)
```

---

## Troubleshooting

### Phone doesn't boot after flashing

- **Check LK2ND**: Make sure LK2ND is properly flashed to both boot_a and boot_b
- **Verify images**: Ensure all images were flashed successfully
- **Check fastboot**: Use `fastboot devices` to verify the phone is detected

### No display output

- The display update service may take a few seconds to start
- Check logs: `journalctl -u display-updater.service`
- Verify framebuffer: `ls -la /dev/fb0`

### External Wi-Fi adapter not detected

- Check USB OTG connection
- Verify adapter is supported by the kernel (check `lsusb` and `dmesg`)
- Ensure the adapter supports monitor mode
- Try different USB Wi-Fi adapters (see compatibility list)

### Modem not working

- Insert a SIM card
- Check ModemManager: `mmcli -L`
- View modem status: `mmcli -m 0`
- Check provisioning: `journalctl -u modem-up.service`

### GPS not working

- GPS **requires a SIM card** to be inserted
- Check service: `systemctl status gps-qcom.service`
- Verify device: `ls -la /dev/ttyUSB9`
- Test NMEA output: `cat /dev/ttyUSB9`

### Build fails

- **Missing dependencies**: Ensure all build tools are installed
- **make_ext4fs not found**: Install from https://github.com/iglunix/make_ext4fs
- **Cross-compiler issues**: Verify `aarch64-linux-gnu-gcc` is in PATH
- **Out of disk space**: Building requires ~10GB of free space

### Unable to flash images

- **Device not detected**: Install fastboot drivers, use `fastboot devices` to check
- **Permission denied**: Run fastboot with sudo or add udev rules
- **Bootloader locked**: Unlock bootloader following Fairphone's official guide

---

## Additional Resources

- **Fairphone 3 Wiki**: https://wiki.postmarketos.org/wiki/Fairphone_3_(fairphone-fp3)
- **Pwnagotchi Documentation**: https://pwnagotchi.ai/
- **LK2ND Project**: https://github.com/msm8916-mainline/lk2nd
- **Qualcomm MSM8953 Mainline**: https://github.com/msm8953-mainline

## Contributing

Contributions are welcome! Please open issues or pull requests on GitHub.

## License

This project uses components from various sources. Check individual files for license information.

---

**Happy Hacking!** 🐾📡

