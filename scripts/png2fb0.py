#!/usr/bin/env python3
import os, time
from PIL import Image

FB = "/dev/fb0"
PNG = "/var/tmp/pwnagotchi.png"

# FP3 framebuffer (from fbset -i)
W, H = 1080, 2160
BPP = 4
STRIDE = 4352           # LineLength
ROW = W * BPP

def img_to_rgb0_bytes(im: Image.Image) -> bytes:
    # Convert to RGBA, scale to screen
    im = im.convert("RGBA").resize((W, H))
    r, g, b, a = im.split()
    # FP3 fbset: rgba 8/16,8/8,8/0,0/0  => bytes are R,G,B,X (little-endian)
    x = Image.new("L", (W, H), 0)
    out = Image.merge("RGBA", (r, g, b, x))  # R,G,B,0
    return out.tobytes()

def push(raw: bytes):
    # rb+ is often more reliable than wb with drm fbdev
    with open(FB, "rb+", buffering=0) as f:
        off = 0
        pad = STRIDE - ROW
        for _ in range(H):
            f.write(raw[off:off+ROW])
            if pad > 0:
                f.write(b"\x00" * pad)
            off += ROW

def main():
    last_mtime = 0
    while True:
        try:
            st = os.stat(PNG)
            if st.st_mtime != last_mtime:
                last_mtime = st.st_mtime
                im = Image.open(PNG)
                raw = img_to_rgb0_bytes(im)
                push(raw)
        except FileNotFoundError:
            pass
        except Exception:
            # tolerate partial writes / decode races
            pass
        time.sleep(0.05)  # fast refresh

if __name__ == "__main__":
    main()

