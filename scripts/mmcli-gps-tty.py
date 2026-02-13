#!/usr/bin/env python3
import os, re, time, signal, subprocess, pty

TTY_LINK = "/dev/ttyUSB9"
OWNER_UID = 0  # root
OWNER_GID = 20 # dialout (Debian/RPi default). If different, change it.
MODE = 0o660

running = True
def stop(*_):
    global running
    running = False

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

def run_cmd(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout

# Enable NMEA (harmless if already enabled)
subprocess.run(["mmcli", "-m", "any", "--location-enable-gps-nmea"],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Create PTY pair
master_fd, slave_fd = pty.openpty()
slave_name = os.ttyname(slave_fd)

# Create stable /dev/ttyUSB9 -> /dev/pts/X
try:
    if os.path.islink(TTY_LINK) or os.path.exists(TTY_LINK):
        try: os.unlink(TTY_LINK)
        except: pass
    os.symlink(slave_name, TTY_LINK)
except Exception as e:
    print(f"[mmcli-gps] failed to create symlink {TTY_LINK} -> {slave_name}: {e}", flush=True)
    raise

try:
    os.chown(TTY_LINK, OWNER_UID, OWNER_GID)
except Exception:
    pass
try:
    os.chmod(TTY_LINK, MODE)
except Exception:
    pass

print(f"[mmcli-gps] PTY slave is {slave_name}, linked as {TTY_LINK}", flush=True)

# Regex for NMEA sentences like $GPGSA..., $GNGNS..., etc
nmea_re = re.compile(r'(\$[A-Z]{2}[A-Z0-9]{3}.*)')

def extract_nmea(mmcli_text: str):
    out = []
    for line in mmcli_text.splitlines():
        m = nmea_re.search(line)
        if m:
            s = m.group(1).strip()
            if s.startswith("$"):
                out.append(s)
    return out

# Write to master; readers read from slave (/dev/pts/X and thus /dev/ttyUSB9)
os.set_blocking(master_fd, True)

while running:
    txt = run_cmd(["mmcli", "-m", "any", "--location-get"])
    nmea = extract_nmea(txt)
    if nmea:
        for s in nmea:
            os.write(master_fd, (s + "\r\n").encode("ascii", "ignore"))
    time.sleep(1)

# Cleanup
try: os.unlink(TTY_LINK)
except: pass
