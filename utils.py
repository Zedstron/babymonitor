import subprocess
import re

import time
import requests
from datetime import datetime
from pathlib import Path

TEST_SERVERS = [
    "https://ash-speed.hetzner.com/10MB.bin",
    "https://sin-speed.hetzner.com/10MB.bin",
    "https://fsn1-speed.hetzner.com/10MB.bin",
]

def quick_speed_test(duration=4):
    best_speed = 0

    for url in TEST_SERVERS:
        try:
            start = time.time()
            downloaded = 0

            with requests.get(url, stream=True, timeout=(5, 10)) as r:
                for chunk in r.iter_content(chunk_size=65536):
                    if not chunk:
                        break

                    downloaded += len(chunk)

                    if time.time() - start >= duration:
                        break

            elapsed = time.time() - start
            mbps = (downloaded * 8) / (elapsed * 1_000_000)
            best_speed = max(best_speed, mbps)

        except requests.exceptions.RequestException:
            continue

    if best_speed == 0:
        return {
            "bandwidth": 0,
            "label": "No Connection"
        }

    if best_speed > 100:
        label = "very fast"
    elif best_speed > 40:
        label = "fast"
    elif best_speed > 10:
        label = "average"
    else:
        label = "slow"

    return {
        "bandwidth": round(best_speed, 2),
        "label": label
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