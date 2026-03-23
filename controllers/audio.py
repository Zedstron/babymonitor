import asyncio
import pyaudio
from pydub import AudioSegment
import numpy as np
import math
from io import BytesIO
from aiortc import MediaStreamTrack
from av.audio.frame import AudioFrame
import subprocess
from fractions import Fraction
import re
import time

class AudioController:
    def __init__(self, rate=48000, channels=1, chunk=960):
        try:
            self.rate = rate
            self.channels = channels
            self.chunk = chunk
            self._audio = pyaudio.PyAudio()
            
            self.open_speaker()
            self.open_mic()
        except Exception as e:
            print("Error initializing Audio", e)

    
    def open_speaker(self):
        try:
            self._speaker = self._audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                output=True,
                frames_per_buffer=self.chunk
            )
        except:
            self._speaker = None
            print("Speakers are not available")
    
    def open_mic(self):
        try:
            self._mic = self._audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
        except:
            self._mic = None
            print("Microphone not Available, Skipping mic")
    
    def update_volume(self, perc):
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{perc}%"])

    def get_volume(self):
        out = subprocess.getoutput("pactl get-sink-volume @DEFAULT_SINK@")
        if '%' in out:
            return int(out.split('/')[1].strip().rstrip('%'))
        return 0

    def play_audio_bytes(self, audio_bytes, mime_type):
        if self._speaker:
            format_map = {
                "audio/ogg": "ogg",
                "audio/webm": "webm",
            }
            audio_format = format_map.get(mime_type, "webm")

            audio = AudioSegment.from_file(BytesIO(audio_bytes), format=audio_format)
            self._speaker.write(audio.raw_data)
            return True
        
        return False

    def guess_occupancy(self):
        return {
            "occupancy": 1,
            "confidence": "98%"
        }

    def get_mic_level(self):
        if not self._mic:
            return { "dbfs": -100, "label": "no input" }

        data = self._mic.read(self.chunk, exception_on_overflow=False)

        samples = np.frombuffer(data, dtype=np.int16)
        rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))

        if rms <= 0:
            db = -100
        else:
            db = 20 * math.log10(rms / 32768)

        db = round(db, 2)

        if db < -55:
            label = "Quiet Room"
        elif db < -45:
            label = "Light Ambient Noise"
        elif db < -35:
            label = "General Noise"
        elif db < -25:
            label = "People Talking"
        elif db < -15:
            label = "Loud Environment"
        else:
            label = "Very Loud / Shouting"

        return {
            "dbfs": db,
            "amplitude": int(rms),
            "label": label
        }

    async def mic_stream(self):
        loop = asyncio.get_running_loop()
        while True:
            data = await loop.run_in_executor(None, self._mic.read, self.chunk, False)
            yield data
    
    def close_mic(self):
        if self._mic:
            self._mic.stop_stream()
            self._mic.close()
            self._mic = None


class MicrophoneTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.samples_per_frame = controller.chunk
        self.sample_rate = controller.rate
        self.timestamp = 0

    async def recv(self):
        await asyncio.sleep(self.samples_per_frame / self.sample_rate)

        if self.controller._mic:
            data = self.controller._mic.read(
                self.samples_per_frame,
                exception_on_overflow=False
            )
            samples = np.frombuffer(data, dtype=np.int16)
        else:
            samples = np.random.randint(
                -32768,
                32767,
                self.samples_per_frame,
                dtype=np.int16
            )

        samples = samples.reshape(1, -1)

        frame = AudioFrame.from_ndarray(samples, format="s16", layout="mono")
        frame.sample_rate = self.sample_rate

        frame.pts = self.timestamp
        frame.time_base = Fraction(1, self.sample_rate)

        self.timestamp += self.samples_per_frame

        return frame