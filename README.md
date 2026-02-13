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
- [Preparing the Pwnagotchi SD Card](#preparing-the-pwnagotchi-sd-card)
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

- **Fairphone 3** (or Fairphone 3+) running Android 13 or later (update to latest official ROM before unlocking bootloader)
- **USB-OTG cable** and **RTL8821CU based USB Wi-Fi adapter** (recommended: EP119 - firmware included in this project)
- **microSD card** (16GB minimum) with Pwnagotchi Raspberry Pi image pre-flashed
- **USB to Ethernet adapter** for initial setup and SSH access
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

## Preparing the Pwnagotchi SD Card

Simply use a standard Pwnagotchi Raspberry Pi SD card image. No need to extract or modify the root filesystem - just flash it to a microSD card and insert it into the Fairphone 3.

### Steps

1. **Download Pwnagotchi Image**
   
   Download the latest Pwnagotchi Raspberry Pi image from:
   - Official releases: https://github.com/evilsocket/pwnagotchi/releases
   - Or use a custom build with your preferred configuration

2. **Flash to SD Card**

   Use your preferred tool to flash the image to a microSD card:
   
   ```bash
   # Using dd (Linux/macOS)
   sudo dd if=pwnagotchi-raspios-lite-v1.5.5.img of=/dev/sdX bs=4M status=progress
   sync
   
   # Or use balenaEtcher, Raspberry Pi Imager, or similar GUI tool
   ```

3. **Insert SD Card into Fairphone 3**

   Power off the phone and insert the microSD card with the flashed Pwnagotchi image.

### Post-Boot Configuration

After the device boots with Fairagotchi, you'll install the necessary services and scripts via SSH. See the [Post-Installation Configuration](#post-installation-configuration) section below for details.

---

## Flashing to Fairphone 3

### Prerequisites

1. **Update to Latest Official ROM**
   
   **IMPORTANT**: Before unlocking the bootloader, ensure your Fairphone 3 is fully updated to the latest official ROM (at least Android 13). This ensures the firmware is up-to-date.

2. **Unlock Bootloader**
   
   Follow the official Fairphone guide:
   https://support.fairphone.com/hc/en-us/articles/360048646311

3. **Boot into Fastboot Mode**
   
   Power off the phone, then hold **Volume Down + Power** until you see the fastboot screen.

### Flashing Process

#### Step 1: Flash LK2ND Bootloader and DTBO (One-time setup)

LK2ND is a secondary bootloader that allows booting mainline Linux kernels. The DTBO (device tree overlay) is flashed here as an empty placeholder - the actual device tree is concatenated to the kernel zImage inside boot.img.

```bash
# Flash LK2ND bootloader
fastboot flash boot_a resources/lk2nd.img
fastboot flash boot_b resources/lk2nd.img

# Flash empty DTBO
fastboot flash dtbo_a resources/dtbo.img
fastboot flash dtbo_b resources/dtbo.img
```

Or use the script (includes dtbo flashing):
```bash
./flash_lk2nd.sh
```

**Note**: The dtbo.img is just an empty placeholder. The real device tree blob (DTB) is concatenated to the zImage inside boot.img during the build process.

Reboot the phone. You should now see the LK2ND boot menu.

#### Step 2: Flash Fairagotchi Kernel and Modules

```bash
./flash.sh
```

Or manually:
```bash
fastboot flash boot images/boot.img
fastboot flash system_a images/modules.img
fastboot flash system_b images/firmware.img
```

**Partition Layout:**
- `boot` - Contains the kernel (zImage with concatenated DTB) and initramfs
- `system_a` - Repurposed to hold kernel modules (mounted at `/lib/modules`)
- `system_b` - Repurposed to hold firmware files (mounted at `/lib/firmware`)
- `dtbo_a/dtbo_b` - Empty placeholder (actual DTB is in boot.img)
- SD card - Root filesystem (Pwnagotchi Raspberry Pi image)

#### Step 3: Insert SD Card and Reboot

1. Power off the phone
2. Insert the microSD card with the Pwnagotchi image
3. Power on the phone

The phone should boot into Fairagotchi and start Pwnagotchi from the SD card!

---

## Post-Installation Configuration

### Accessing the Device

1. **Via USB to Ethernet Adapter**
   
   Connect a USB to Ethernet adapter to the phone using a USB-OTG cable, then connect an Ethernet cable from the adapter to your computer or network.
   
   Once connected, SSH into the device:
   
   ```bash
   ssh pi@10.0.0.2
   # Default password: raspberry
   ```

   **Note**: USB-C role switching for USB ethernet (like the original Pwnagotchi) will be implemented in the future.

2. **Via Serial Console** (if USB networking doesn't work)
   
   You may need a USB serial adapter connected to the phone's debugging pins.

### Installing Fairagotchi Services and Scripts

After you've successfully booted into Pwnagotchi and can SSH into the device, install the Fairagotchi-specific components:

1. **Copy Files to the Device**

   From your build machine, copy the necessary files:

   ```bash
   # Copy helper scripts
   scp scripts/png2fb0.py pi@10.0.0.2:/tmp/
   scp scripts/mmcli-gps-tty.py pi@10.0.0.2:/tmp/
   scp scripts/qmi-provision.sh pi@10.0.0.2:/tmp/
   
   # Copy systemd services
   scp systemd-services/*.service pi@10.0.0.2:/tmp/
   
   # Copy display plugin
   scp plugins/display.py pi@10.0.0.2:/tmp/
   ```

2. **Install on the Device**

   SSH into the device and run:

   ```bash
   # Move scripts to proper locations
   sudo mv /tmp/png2fb0.py /usr/local/bin/
   sudo mv /tmp/mmcli-gps-tty.py /usr/local/sbin/
   sudo mv /tmp/qmi-provision.sh /usr/local/sbin/
   sudo chmod +x /usr/local/bin/png2fb0.py
   sudo chmod +x /usr/local/sbin/mmcli-gps-tty.py
   sudo chmod +x /usr/local/sbin/qmi-provision.sh
   
   # Install systemd services
   sudo mv /tmp/*.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable display-updater.service gps-qcom.service modem-up.service
   sudo systemctl start display-updater.service gps-qcom.service modem-up.service
   ```

3. **Replace Display Plugin**

   Find the location of the display.py file:

   ```bash
   find /home/pi -name "display.py" 2>/dev/null | grep pwnagotchi
   # Or search more broadly if not found:
   # sudo find / -name "display.py" 2>/dev/null | grep pwnagotchi
   ```

   This will show you the path, typically something like:
   `/home/pi/.local/lib/python3.9/site-packages/pwnagotchi/ui/display.py`

   Replace it with the Fairagotchi version:

   ```bash
   # Backup the original
   sudo cp /path/to/original/display.py /path/to/original/display.py.backup
   
   # Replace with Fairagotchi version
   sudo cp /tmp/display.py /path/to/original/display.py
   ```

4. **Disable Automatic Pwnagotchi Updates**

   To prevent automatic updates from overwriting your custom display.py:

   ```bash
   sudo systemctl disable pwnagotchi-auto-update
   sudo systemctl stop pwnagotchi-auto-update
   ```

   Or edit the Pwnagotchi configuration:

   ```bash
   sudo nano /etc/pwnagotchi/config.toml
   ```

   Add or modify:
   ```toml
   main.update.enabled = false
   ```

   **Note**: A separate display plugin that doesn't require modifying Pwnagotchi itself will be developed in the future.

5. **Install Additional Dependencies**

   Install the required packages for modem, GPS, and other functionality:

   ```bash
   sudo apt-get update
   sudo apt-get install -y \
       modemmanager \
       libqmi-utils \
       rmtfs \
       python3-pil \
       linux-firmware \
       network-manager
   ```

   **Package explanations:**
   - `modemmanager` - Manages the Qualcomm modem
   - `libqmi-utils` - QMI protocol utilities for modem communication (includes `qmicli`)
   - `rmtfs` - Remote filesystem service for modem firmware access
   - `python3-pil` - Python Imaging Library for display rendering
   - `linux-firmware` - Must be reinstalled as the init script removes original firmware from rootfs
   - `network-manager` - For managing network connections (includes `nmcli`)

   **Why reinstall linux-firmware?**
   The initramfs script (`/init`) removes `/lib/firmware` from the rootfs and replaces it with a mount from the `system_b` partition. This ensures the kernel uses the firmware included in this project, but you may want additional firmware packages for other hardware.

6. **Customize QMI Provisioning AID (if needed)**

   The modem provisioning service uses a specific AID (Application Identifier) for the SIM card. The default AID in `/usr/local/sbin/qmi-provision.sh` is:

   ```
   AID="A0:00:00:00:87:10:02:FF:49:94:20:89:03:10:00:00"
   ```

   This works for most SIM cards, but if your modem doesn't initialize correctly, you may need to find and use the correct AID for your SIM card. You can list available AIDs with:

   ```bash
   qmicli -d qrtr://0 --uim-get-card-status
   ```

   If you need to change it, edit the script:

   ```bash
   sudo nano /usr/local/sbin/qmi-provision.sh
   ```

7. **Reboot**

   ```bash
   sudo reboot
   ```

### Configure Pwnagotchi for External Wi-Fi

Edit the Pwnagotchi configuration to use your RTL8821CU USB Wi-Fi adapter:

```bash
sudo nano /etc/pwnagotchi/config.toml
```

Update the interface name to match your USB adapter (usually `wlan1`):
```toml
main.iface = "wlan1"
```

### Configure External USB Wi-Fi Adapter

1. Plug in your RTL8821CU USB Wi-Fi adapter (e.g., EP119) via OTG cable
2. Verify it's detected:
   ```bash
   ip link show
   # Should show wlan1 or similar
   lsusb
   # Should show your RTL8821CU adapter
   ```
3. The firmware for RTL8821CU is included in this project

### Configure Mobile Data (Optional)

If you want to use the internal modem for internet connectivity:

1. **Insert a SIM card** into the phone

2. **Wait for modem initialization**
   
   The `modem-up.service` should automatically provision the modem. Check status:
   
   ```bash
   systemctl status modem-up.service
   mmcli -L  # List modems
   mmcli -m 0  # Check modem 0 status
   ```

3. **Configure APN with NetworkManager**

   Use `nmcli` to create a connection profile for your mobile provider:

   ```bash
   # Example for a generic provider
   sudo nmcli connection add \
       type gsm \
       ifname '*' \
       con-name mobile \
       apn "your-apn-here" \
       connection.autoconnect yes
   
   # For some providers, you may also need username/password:
   # sudo nmcli connection modify mobile gsm.username "your-username"
   # sudo nmcli connection modify mobile gsm.password "your-password"
   ```

   **Common APN examples** (verify with your carrier as these may change):
   - T-Mobile US: `fast.t-mobile.com`
   - AT&T US: `phone`
   - Verizon US: `vzwinternet`
   - Vodafone: `internet`
   
   Contact your mobile provider for the correct APN settings.

4. **Activate the connection**

   ```bash
   sudo nmcli connection up mobile
   ```

   The connection will now automatically connect on boot thanks to `connection.autoconnect yes`.

5. **Verify connectivity**

   ```bash
   ip addr show wwan0  # Check if interface has an IP
   ping -I wwan0 8.8.8.8  # Test connectivity
   ```

### Security Warning: Public IP Access

**IMPORTANT**: When using mobile data, your device may be directly accessible via a public IP address. This is a security risk, especially for Pwnagotchi which exposes services on various ports.

**Recommended: Configure firewall rules**

Block incoming connections to Pwnagotchi ports:

```bash
# Install iptables if not present
sudo apt-get install -y iptables iptables-persistent

# Block incoming connections on Pwnagotchi web interface (port 8080)
sudo iptables -A INPUT -i wwan0 -p tcp --dport 8080 -j DROP

# Block incoming connections on Pwnagotchi API (port 8081)
sudo iptables -A INPUT -i wwan0 -p tcp --dport 8081 -j DROP

# Allow established connections (responses to your outgoing requests)
sudo iptables -A INPUT -i wwan0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Optional: Block all other incoming connections on mobile interface
# sudo iptables -A INPUT -i wwan0 -j DROP

# Save rules so they persist across reboots
sudo netfilter-persistent save
```

Alternatively, configure Pwnagotchi to only listen on the USB interface (`usb0`) instead of all interfaces.

### Configure GPS (Optional)

GPS requires a SIM card to be inserted (due to Qualcomm firmware requirements).

**How it works**: The `gps-qcom.service` runs the `mmcli-gps-tty.py` script, which:
- Uses Python's `pty` module to create a pseudo-terminal pair
- Reads NMEA sentences from ModemManager (`mmcli -m any --location-get`)
- Writes them to a PTY, creating a virtual serial device
- Creates a symlink `/dev/ttyUSB9` -> `/dev/pts/X` for compatibility

**Configuration steps:**

1. Ensure the GPS service is running:
   ```bash
   systemctl status gps-qcom.service
   ```

2. Verify the virtual serial device exists:
   ```bash
   ls -la /dev/ttyUSB9
   # Should show: /dev/ttyUSB9 -> /dev/pts/X
   ```

3. Test GPS output:
   ```bash
   cat /dev/ttyUSB9
   # Should show NMEA sentences like $GPGGA, $GPRMC, etc.
   ```

4. Configure Pwnagotchi to use the GPS device in `/etc/pwnagotchi/config.toml`:
   ```toml
   main.plugins.gps.enabled = true
   main.plugins.gps.device = "/dev/ttyUSB9"
   main.plugins.gps.speed = 19200
   ```

### Display Updates

The custom `display.py` plugin exports PNG frames to `/var/tmp/pwnagotchi.png`.
The `png2fb0.py` script (run by `display-updater.service`) continuously pushes these frames to the phone's framebuffer (`/dev/fb0`).

---

## Using with Other ARM64 Linux Distributions

This project isn't limited to Pwnagotchi! You can use it to boot any ARM64 Linux distribution from the SD card on the Fairphone 3.

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
   - Flash your ARM64 Linux distribution image to a microSD card
   - Or use a pre-configured SD card image for your chosen distribution
4. **Insert the SD card** into the Fairphone 3
5. **Reboot** and enjoy your chosen Linux distribution!

### Example: PostmarketOS

```bash
# Download PostmarketOS image for your preferred UI
# Flash it to SD card
sudo dd if=postmarketos-fairphone-fp3.img of=/dev/sdX bs=4M status=progress

# Insert into phone and boot
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
- **Recommended**: Use an RTL8821CU based adapter (e.g., EP119) - firmware is included in this project
- Ensure the adapter supports monitor mode
- Check if the driver is loaded: `lsmod | grep rtl`

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

