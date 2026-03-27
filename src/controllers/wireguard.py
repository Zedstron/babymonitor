import os
import subprocess
import secrets
import string

class WireGuard:
    def __init__(self, iface="wg0"):
        self.iface = iface
        self.config_path = f"/etc/wireguard/{iface}.conf"
        self.private_key_path = f"{self.config_path}.private"
        self.public_key_path = f"{self.config_path}.public"

        try:
            if not os.path.exists(self.private_key_path) or not os.path.exists(self.public_key_path):
                self._generate_keys()
        except Exception as e:
            print("Wireguard Config Failed, Possibly wireguard not found or platform not supported", str(e))

    def _generate_keys(self):
        private_key = subprocess.run(
            ["wg", "genkey"], input=None, capture_output=True, text=True
        )

        if private_key.returncode != 0:
            b64_chars = string.ascii_letters + string.digits + "+/"
            private_key = ''.join(secrets.choice(b64_chars) for _ in range(44))
        else:
            private_key = private_key.stdout.strip()

        with open(self.private_key_path, "w") as f:
            f.write(private_key)

        result = subprocess.run(
            ["wg", "pubkey"],
            input=private_key.encode(),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError("Failed to generate public key from private key.")

        public_key = result.stdout.strip()

        with open(self.public_key_path, "w") as f:
            f.write(public_key)

    def get_config(self):
        config = { "public_key": "", "is_active": self.__is_running() }

        try:
            config["public_key"] = open(self.public_key_path).read().strip()
        except:
            pass

        if not os.path.exists(self.config_path):
            return config

        current_section = None
        with open(self.config_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1]
                    config[current_section] = {}
                elif "=" in line and current_section:
                    k, v = map(str.strip, line.split("=", 1))
                    if k.lower() != "privatekey":
                        config[current_section][k] = v
        return config

    def save_config(self, config_dict):
        """
        Accept a dict with full WireGuard config params:
        {
            'Address': '10.0.0.1/24',
            'ListenPort': '51820',
            'PeerPublicKey': 'client_public_key',
            'AllowedIPs': '10.0.0.2/32',
            'Endpoint': '1.2.3.4:51820', # optional
            'PersistentKeepalive': '25'  # optional
        }
        """
        try:
            private_key = open(self.private_key_path).read().strip()

            lines = [
                "[Interface]",
                f"Address = {config_dict.get('Address', '10.0.0.1/24')}",
                f"ListenPort = {config_dict.get('ListenPort', '51820')}",
                f"PrivateKey = {private_key}",
                "",
                "[Peer]",
                f"PublicKey = {config_dict['PeerPublicKey']}",
                f"AllowedIPs = {config_dict.get('AllowedIPs', '10.0.0.2/32')}"
            ]

            if "Endpoint" in config_dict:
                lines.append(f"Endpoint = {config_dict['Endpoint']}")

            if "PersistentKeepalive" in config_dict:
                lines.append(f"PersistentKeepalive = {config_dict['PersistentKeepalive']}")

            with open(self.config_path, "w") as f:
                f.write("\n".join(lines) + "\n")
            
            return True
        except:
            return False

    def start(self):
        try:
            r1 = subprocess.run(["wg-quick", "up", self.iface])
            r2 = subprocess.run(["systemctl", "enable", f"wg-quick@{self.iface}"])

            return r1.returncode == 0 and r2.returncode == 0
        except:
            return False

    def stop(self):
        try:
            r1 = subprocess.run(["wg-quick", "down", self.iface])
            r2 = subprocess.run(["systemctl", "disable", f"wg-quick@{self.iface}"])

            return r1.returncode == 0 and r2.returncode == 0
        except:
            return False

    def __is_running(self):
        try:
            result = subprocess.run(
                ["wg", "show", self.iface],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return result.returncode == 0
        except:
            return False