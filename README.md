# 🍼 BabyGuard — Smart Raspberry Pi Baby Monitor

<p align="center">
  <img src="src/assets/img/banner.png" alt="BabyGuard Banner" width="100%"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Raspberry%20Pi-blue">
  <img src="https://img.shields.io/badge/backend-FastAPI-teal">
  <img src="https://img.shields.io/badge/streaming-WebRTC-orange">
  <img src="https://img.shields.io/badge/status-Active%20Development-yellow">
  <img src="https://img.shields.io/badge/license-MIT-green">
</p>

---

## 🚀 Overview
**BabyGuard** is a Raspberry Pi–powered smart baby monitoring system built using **FastAPI + WebRTC** for ultra-low latency streaming.

✔ Works over **LAN + WAN**  
✔ Designed for **real-time monitoring + interaction**  
✔ Lightweight, self-hosted, privacy-first
✔ Can Control Infrared Devices

---

## ✨ Features

### 🎥 Monitoring
- Live camera feed *(Pi Camera optional)*
- Live microphone streaming *(optional)*
- WebRTC ultra-low latency

### 🌡️ Environment
- Temperature & humidity monitoring
- Outside weather integration

### 🎙️ Interaction
- Push to TALK
- Media Player for child soothing
- White Noise for Sleep

### 💡 Hardware
- LED Indicator (via GPIO)
- Temp/Humid Sensor (via GPIO)
- Buzzer indicator (via GPIO)
- Microphone Support (via USB)
- Camera Module (via CSI Port)
- TSOP Receiver for IR Learning (via GPIO)
- IR Sender LED (via GPIO)

### 📊 System Monitoring
- CPU, RAM, disk, network stats
- Full Raspberry Pi health dashboard

### 🎞️ Media
- Video recording
- Playback interface
- Snapshot capture + gallery

### 🔐 Security
- JWT Authentication

---

## 📸 Screenshots

<p align="center">
  <b>Main Interaction Dashboard</b><br /><br />
  <img src="src/assets/img/screenshot1.png" width="90%"/>
</p>
<p align="center">
  <b>Mediaplayer & Snapshots Gallery</b><br /><br />
  <img src="src/assets/img/screenshot2.png" width="45%"/>
</p>
<p align="center">
  <b>Resource Usage Tracking</b><br /><br />
  <img src="src/assets/img/screenshot4.png" width="90%"/>
</p>

---

## 🧠 Architecture (WAN Setup)

<p align="center">
  <b>Wireguard Secure VPN & Caddy Reverse Proxy Config</b><br /><br />
  <img src="src/assets/img/architecture.png" width="80%"/>
</p>

### 🔗 Flow
1. Client connects via domain → Caddy (TLS termination)
2. Caddy reverse proxies to backend
3. WireGuard tunnel connects VPS → Home network (Private Secure VPN)
4. Raspberry Pi (behind NAT) streams via WebRTC

---

## 🔌 GPIO & Hardware Guidelines

> **Note:** All components are recommended for the best experience, but none are mandatory. If you omit a specific part (e.g., IR sender/receiver or mic/camera), only that specific functionality will be unavailable. Everything else will work seamlessly.

<p align="center">
  <b>CSI Camera Module</b><br><br>
  <img src="src/assets/img/hardware_camera.png" width="90%"/>
</p>

<p align="center">
  <b>GPIO Pinout Details</b><br><br>
  <img src="src/assets/img/hardware_pinout.png" width="90%"/>
</p>

<p align="center">
  <b>Components Schematic Diagram</b><br><br>
  <img src="src/assets/img/hardware_schematic.png" width="90%"/>
</p>

- LED Indicator wiring (GPIO pins)
- DHT22/DHT11 (Temp/Humidity) (GPIO pins)
- Piezo Buzzer (GPIO pins)
- Speakers integration (3.5mm Audio Jack)
- Microphone integration (USB port 2.0 or 3.0)
- Camera module (CSI camera port)
- TSOP IR Reciver sensor (GPIO pins)
- IR sender sensor (GPIO pins)

---

Automatic installation is recommended hence there are mnay steps involved installing system wide global packags and setting up proper boot service and other optimizations e.g. enabling/disabling other required hardware capablitities & features, the included setup.sh script takes care of this automatically.

## 🛠️ Automatic Installation (Recommended)

### 1. Clone
```bash
git clone https://github.com/Zedstron/babymonitor
cd babymonitor
```

### 2. Run Setup
```bash
sudo chmod +x setup.sh
sudo ./setup.sh
```
---

Or if automatic installation isn't working for you, or crashes or packages broken or any thing
in general go wrong try following Manual minimal steps.

## 🛠️ Manuall Installation

### 1. Clone
```bash
git clone https://github.com/Zedstron/babymonitor
cd babymonitor
```

### 2. Update & Upgrade APT repo
```bash
sudo apt update -y
sudo apt upgrade -y
```

### 3. Virtual Env
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Packages
Install Python Packages
```bash
pip install -r requirements.txt
```

Install System Deps:
```bash
sudo apt install -y $(cat packages.txt)
```

### 5. ENV File
Create the .env file with nano or any text editor of your choice and place following variables

```bash
JWT_SECRET="any alphanumeric strong random value for JWT"
WEATHER_API_KEY="optional key for current latest weahter"
```

> Note: Obtain a weather API key at https://home.openweathermap.org/users/sign_in just in case if you are interested in this feature

### 6. SSL
Generate certificates for https, since for PTT to work we cannot access microphone in browser from http, permission won't be allowed

```bash
mkdir cert
cd cert
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
```
---

## ▶️ Run
```bash
python main.py
```
---

An experimental Docker image is published to Docker Hub. This method is NOT Recommended for production and is provided for quick testing only.

## ⚠️ Docker (Experimental)

Before running the container, ensure a `.env` file exists in the project root containing at minimum a `JWT_SECRET`. You may also include an optional `WEATHER_API_KEY` (if omitted, external weather won't be available). You can obtain a weather API key at https://home.openweathermap.org/users/sign_in

Pull the image from Docker Hub:

```bash
docker pull zedstron/babyguard
```

Example run (reads variables from `.env`):

```bash
docker run --env-file .env -p 443:443 zedstron/babyguard
```
---

## 🔮 Roadmap
- Cry detection (AI)
- Occupancy detection (Vision or Motion Sensor)
- Push notifications
- Facial emotions detection e.g. not feeling comfortable
- Baby heavy movement e.g. moving outside crib
- Converting FE side to React/Angular

---

## 🤝 Contributing
PRs Welcom