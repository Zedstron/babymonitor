import numpy as np
import pyaudio
import threading

class WhiteNoisePlayer:
    def __init__(self, rate=44100, chunk=1024):
        self.rate = rate
        self.chunk = chunk
        self.running = False

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.rate,
            output=True
        )

        self.thread = None

    def _play(self):
        while self.running:
            noise = np.random.uniform(-1, 1, self.chunk).astype(np.float32)
            self.stream.write(noise.tobytes())

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._play, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.__close()

    def __close(self):
        self.stop()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()