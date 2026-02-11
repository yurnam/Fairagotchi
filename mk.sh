#!/bin/bash
set -euo pipefail

export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-

DTB="qcom/sdm632-fairphone-fp3.dts"
defconfig="fp3.config"

# Image sizes for make_ext4fs (-l)
modules_size="120M"      # was dd count=100 bs=1M
firmware_size="120M"
rootfs_size="10000M"     # (kept in case you use it later)

VMLINUX_DIR="linux"
AIK_DIR="aik"
IMAGES_DIR="images"

MOD_STAGING="./MODTEMP"  # staging dir for modules_install (no mount needed)

mkdir -p "${IMAGES_DIR}"

cd "${VMLINUX_DIR}"

if [ -f ".config" ]; then
  make xconfig
else
  make "${defconfig}"
fi

make -j"$(nproc)"

cd ..

# Build zImage-dtb and copy into AIK split_img
cat "${VMLINUX_DIR}/arch/arm64/boot/Image.gz" \
    "${VMLINUX_DIR}/arch/arm64/boot/dts/${DTB}" \
  > "${VMLINUX_DIR}/zImage-dtb"

cp "${VMLINUX_DIR}/zImage-dtb" "${AIK_DIR}/split_img/boot.img-zImage"

# ---- Build modules.img WITHOUT mounting (using make_ext4fs) ----
rm -rf "${MOD_STAGING}"
mkdir -p "${MOD_STAGING}"

# Install modules into staging directory
cd "${VMLINUX_DIR}"
make modules_install \
  INSTALL_MOD_PATH="../${MOD_STAGING}" \
  INSTALL_MOD_STRIP=1
cd ..

# (Optional) If you want /lib/modules at the image root (as your old script did),
# flatten one level: move lib/modules/* -> /
if [ -d "${MOD_STAGING}/lib/modules" ]; then
  shopt -s dotglob nullglob
  mv "${MOD_STAGING}/lib/modules/"* "${MOD_STAGING}/" || true
  rm -rf "${MOD_STAGING}/lib"
  shopt -u dotglob nullglob
fi

# Create ext4 image from directory contents (no mount)
# -s  sparse image
# -l  image length
# -a  mount point inside image ("/" is fine)
make_ext4fs -s -l "${modules_size}" -a / "${IMAGES_DIR}/modules.img" "${MOD_STAGING}"

# Clean staging
rm -rf "${MOD_STAGING}"

# ---- Repack boot image ----
cd "${AIK_DIR}"
./repackimg_x64.sh
mv image-new.img "../${IMAGES_DIR}/boot.img"
cd ..

# ---- Firmware image (as before) ----
make_ext4fs -s -l "${firmware_size}" "${IMAGES_DIR}/firmware.img" firmware

# ---- Rootfs cleanup (as before) ----
rm -rf rootfs/dev/* 2>/dev/null || true
rm -rf rootfs/tmp/* 2>/dev/null || true
rm -rf rootfs/run/* 2>/dev/null || true
