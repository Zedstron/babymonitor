import subprocess
import tempfile
from os import unlink
from helpers.logger import logger
from helpers.database import save_ir_device, get_ir_device


class IRController:
    def __init__(self, lirc_dev="/dev/lirc0", freq=38000):
        self.lirc_dev = lirc_dev
        self.default_freq = freq
        logger.info("IR Controller has been initialized")

    def record(self, tag, duration=3, frequency=None):
        logger.debug(f"Attempting to record signal for {tag} at {frequency} for {duration}sec")
        cmd = ["timeout", str(duration), "mode2", "-d", self.lirc_dev]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)

        pulses = []
        for line in proc.stdout:
            parts = line.strip().split()
            if len(parts) == 2:
                _, value = parts
                pulses.append(int(value))

        pulses = self.__clean(pulses)
        if len(pulses) > 0:
            return save_ir_device(tag, " ".join(pulses), frequency or self.default_freq)

        return False

    def __clean(self, pulses, min_len=10):
        if len(pulses) < min_len:
            return []

        while pulses and pulses[0] < 100:
            pulses.pop(0)

        return pulses

    def send(self, id, frequency=None):
        try:
            device = get_ir_device(id)
            if not device:
                return "Device not Found"

            freq = frequency or device["frequency"]
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                f.write(f"carrier {freq}\n")
                f.write(device["signal"])
                fname = f.name

            cmd = ["ir-ctl", "-d", self.lirc_dev, "--send=" + fname]
            subprocess.run(cmd)

            try:
                unlink(fname)
            except:
                pass
        except Exception as e:
            return False