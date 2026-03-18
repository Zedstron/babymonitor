import asyncio
from enum import Enum
from typing import Optional
import logging

try:
    from gpiozero import LED, Buzzer
    import adafruit_dht
    import board
    PI_AVAILABLE = True
except ImportError:
    PI_AVAILABLE = False

logger = logging.getLogger(__name__)


class IndicatorColor(Enum):
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"

class IndicatorState(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLINK = "blink"

class GPIOController:

    PINS = {
        "red": 17,
        "green": 27,
        "yellow": 22,
        "buzzer": 23,
        "dht_pin": 4
    }

    def __init__(self):
        self._components = {}
        self._dht = None
        if PI_AVAILABLE:
            self._components["red"] = LED(self.PINS["red"])
            self._components["green"] = LED(self.PINS["green"])
            self._components["yellow"] = LED(self.PINS["yellow"])
            self._components["buzzer"] = Buzzer(self.PINS["buzzer"])
            try:
                self._dht = adafruit_dht.DHT22(board.D4)
            except:
                self._dht = None

    def read_sensors(self):
        temp = None
        hum = None
        if self._dht:
            try:
                t = self._dht.temperature
                h = self._dht.humidity
                if t is not None:
                    temp = round(t, 1)
                if h is not None:
                    hum = round(h, 1)
            except:
                pass
        return {"temp": temp, "humidity": hum}

    async def beep(self, duration: float, frequency: int):
        if "buzzer" not in self._components:
            return
        self._components["buzzer"].on()
        await asyncio.sleep(duration)
        self._components["buzzer"].off()

    def enable_ir(self, enable: bool):
        if "yellow" not in self._components:
            return
        if enable:
            self._components["yellow"].on()
        else:
            self._components["yellow"].off()

    def _all_off(self):
        for k in ["red", "green", "yellow"]:
            if k in self._components:
                self._components[k].off()

    def set_indicator(self, color: IndicatorColor, state: IndicatorState, blink_pulse: Optional[int] = None, delay_before_next_pulse: Optional[int] = None):
        if color.value not in self._components:
            return

        led = self._components[color.value]
        if state == IndicatorState.ACTIVE:
            self._all_off()
            led.on()
        elif state == IndicatorState.INACTIVE:
            led.off()
        elif state == IndicatorState.BLINK:
            async def _blink():
                while True:
                    led.on()
                    await asyncio.sleep((blink_pulse or 500) / 1000)
                    led.off()
                    await asyncio.sleep((delay_before_next_pulse or 500) / 1000)
            asyncio.create_task(_blink())
        elif state == IndicatorState.blink_pulse:
            async def _pulse():
                led.on()
                await asyncio.sleep((blink_pulse or 200) / 1000)
                led.off()
                await asyncio.sleep((delay_before_next_pulse or 1000) / 1000)
            asyncio.create_task(_pulse())