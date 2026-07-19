import asyncio
import pyaudio
import numpy as np
import math
import os
import vlc
import tempfile
import time
from aiortc.mediastreams import AUDIO_PTIME
from aiortc import MediaStreamTrack
from av.audio.frame import AudioFrame
from fractions import Fraction
import subprocess

class AudioController:
    def __init__(self, rate=48000, channels=1, chunk=960):
        try:
            self.rate = rate
            self.channels = channels
            self.chunk = chunk
            self._audio = pyaudio.PyAudio()

            self.open_mic()
        except Exception as e:
            print("Error initializing Audio", e)

    
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
        ext_map = { "audio/ogg": ".ogg", "audio/webm": ".webm" }
        ext = ext_map.get(mime_type, ".webm")

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(audio_bytes)
            temp_filename = f.name

        try:
            player = vlc.MediaPlayer(temp_filename)
            player.play()

            while player.get_state() != vlc.State.Ended:
                time.sleep(0.1)
            
            return True
        except:
            return False
        finally:
            os.remove(temp_filename)

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

        self.pts = 0
        self.loop = asyncio.get_running_loop()

    async def recv(self):
        data = await self.loop.run_in_executor(
            None,
            self.controller._mic.read,
            self.samples_per_frame,
            False
        )

        frame = AudioFrame(
            format="s16",
            layout="mono",
            samples=self.samples_per_frame,
        )

        frame.planes[0].update(data)
        frame.sample_rate = self.sample_rate
        frame.time_base = Fraction(1, self.sample_rate)
    
        frame.pts = self.pts
        self.pts += self.samples_per_frame
    
        return frame