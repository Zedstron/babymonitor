import subprocess
import re

import socket
import hashlib
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from helpers.database import User
from speedtest import Speedtest

def sp_to_label(speed):
    if speed > 100:
        label = "Very Fast"
    elif speed > 40:
        label = "Fast"
    elif speed > 10:
        label = "Average"
    else:
        label = "Slow"
    
    return label

def quick_speed_test():
    st = Speedtest()
    st.get_servers()
    st.get_best_server()
    download_speed = st.download() / 1_000_000
    upload_speed = st.upload() / 1_000_000

    if download_speed == 0:
        return {
            "download": { "speed": 0, "label": "No Connection" },
            "upload": { "speed": 0, "label": "No Connection" }
        }

    return {
        "download": { "speed": round(download_speed, 2), "label": sp_to_label(download_speed) },
        "upload": { "speed": round(upload_speed, 2), "label": sp_to_label(upload_speed) }
    }

def get_wifi_signal(interface="wlan0"):
    try:
        result = subprocess.check_output(["iwconfig", interface], stderr=subprocess.DEVNULL).decode()

        match = re.search(r"Signal level=(-?\d+)", result)
        if not match:
            return None

        dbm = int(match.group(1))

        percent = max(0, min(100, 2 * (dbm + 100)))

        bars = min(4, max(0, int(percent / 25)))

        return {
            "dbm": dbm,
            "signalStrength": percent,
            "bars": bars
        }

    except Exception:
        return {
            "dbm": 0,
            "signalStrength": 0,
            "bars": 0
        }

def ts_filename(prefix="recording", ext="mp4"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{ext}"

def get_storage(path):
    p = Path(path)
    if not p.exists():
        return 0

    total = 0
    for f in p.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except Exception:
                pass
    return format_bytes(total)

def format_bytes(size):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}" if unit != "B" else f"{size} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def get_latency(host="8.8.8.8"):
    try:
        result = subprocess.check_output(
            ["ping", "-c", "1", "-W", "1", host],
            stderr=subprocess.DEVNULL
        ).decode()

        match = re.search(r"time=([\d\.]+)\s*ms", result)
        if not match:
            return None

        latency = float(match.group(1))

        if latency < 30:
            label = "excellent"
        elif latency < 60:
            label = "good"
        elif latency < 120:
            label = "ok"
        else:
            label = "slow"

        return {
            "latency": latency,
            "label": label
        }

    except Exception:
        return {
            "latency": None,
            "label": None
        }

def format_uptime(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"

def check_new_install(db: Session):
    return db.query(User).count() == 0

def get_hostname():
    return socket.gethostname()

def set_hostname(new_hostname: str):
    if not new_hostname or len(new_hostname) > 253:
        raise ValueError("Invalid hostname")

    subprocess.run(
        ["hostnamectl", "set-hostname", new_hostname],
        check=True
    )

    try:
        with open("/etc/hosts", "r") as f:
            lines = f.readlines()

        with open("/etc/hosts", "w") as f:
            for line in lines:
                if "127.0.1.1" in line:
                    f.write(f"127.0.1.1\t{new_hostname}\n")
                else:
                    f.write(line)
    except Exception:
        return False

    return True