#!/usr/bin/env bash
set -euo pipefail

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  echo "This script needs sudo; re-running with sudo..."
  exec sudo bash "$0" "$@"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_USER="${SUDO_USER:-$(logname 2>/dev/null || echo pi)}"

echo "Project dir: $SCRIPT_DIR"
echo "Run script as $RUN_USER"

echo "Updating APT Packages ..."
apt update -y

echo "Upgrading APT Packages ..."
apt upgrade -y

echo "Disabling Bluetooth..."
systemctl disable --now bluetooth.service || true
systemctl mask bluetooth.service || true
systemctl disable --now hciuart.service || true
rfkill block bluetooth || true

CONFIG_LINE='dtoverlay=pi3-disable-bt'
if ! grep -qF "$CONFIG_LINE" /boot/config.txt 2>/dev/null; then
  echo "$CONFIG_LINE" >> /boot/config.txt
  echo "Added $CONFIG_LINE to /boot/config.txt"
fi

PKG_FILE="$SCRIPT_DIR/packages.txt"
if [ -f "$PKG_FILE" ]; then
  echo "Installing system packages from packages.txt..."
  mapfile -t PKGS < <(grep -Ev '^\s*(#|$)' "$PKG_FILE")
  if [ "${#PKGS[@]}" -gt 0 ]; then
    apt install -y --no-install-recommends "${PKGS[@]}"
  else
    echo "No packages listed in packages.txt"
  fi
else
  echo "packages.txt not found; skipping system package install"
fi

echo "Creating Python virtual environment and installing requirements..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found; please install Python 3 and rerun. Exiting."
  exit 1
fi

sudo -u "$RUN_USER" -H bash -lc "python3 -m venv '$SCRIPT_DIR/venv'"
sudo -u "$RUN_USER" -H bash -lc "source '$SCRIPT_DIR/venv/bin/activate' && python -m pip install --upgrade pip && python -m pip install -r '$SCRIPT_DIR/requirements.txt' || true"

echo "Creating .env file with SECRET_KEY and OPENWEATHER_KEY (empty)..."
sudo -u "$RUN_USER" -H bash -lc '
  SECRET_KEY=$(openssl rand -base64 32 2>/dev/null | tr -dc "A-Za-z0-9" | head -c 32 || python3 -c "import secrets,string; print(\"\".join(secrets.choice(string.ascii_letters+string.digits) for _ in range(32)))")
  umask 077
  cat > "'$SCRIPT_DIR'/.env" <<EOL
SECRET_KEY=$SECRET_KEY
OPENWEATHER_KEY=
EOL
'
chmod 600 "$SCRIPT_DIR/.env"
chown "$RUN_USER":"$RUN_USER" "$SCRIPT_DIR/.env" || true

echo "Generating certificates (interactive openssl prompt may appear)..."
CERT_DIR="$SCRIPT_DIR/cert"
if [ ! -d "$CERT_DIR" ] || [ -z "$(ls -A "$CERT_DIR" 2>/dev/null)" ]; then
  sudo -u "$RUN_USER" -H bash -lc "mkdir -p '$CERT_DIR' && cd '$CERT_DIR' && openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes"
else
  echo "Certificate directory already exists and is not empty; skipping cert generation"
fi

SERVICE_PATH="/etc/systemd/system/babymonitor.service"
echo "Creating systemd service at $SERVICE_PATH"
cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=BabyMonitor service
After=network.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$SCRIPT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

chmod 644 "$SERVICE_PATH"
systemctl daemon-reload
systemctl enable --now babymonitor.service || true

echo "Updating the Rpi hostname"
hostnamectl set-hostname babyguard

printf "\n\033[32m
  ____       _                   ____                      _      _           _ 
 / ___|  ___| |_ _   _ _ __     / ___|___  _ __ ___  _ __ | | ___| |_ ___  __| |
 \___ \ / _ \ __| | | | '_ \   | |   / _ \| '_ ` _ \| '_ \| |/ _ \ __/ _ \/ _` |
  ___) |  __/ |_| |_| | |_) |  | |__| (_) | | | | | | |_) | |  __/ ||  __/ (_| |
 |____/ \___|\__|\__,_| .__/    \____\___/|_| |_| |_| .__/|_|\___|\__\___|\__,_|
                      |_|                           |_|                                              

                [Setup Completed, Read following before continue further]

        1) Access using https://babyguard.local or LAN IP address with https
        2) It is Highly Recomended to restart the device now.
        3) Make sure your phone/tablet is on same network as of this device
        4) If WAN access is required make sure you have a VPS and open the Frontend to enable WAN mode
\033[0m\n"