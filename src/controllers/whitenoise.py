import numpy as np
import pyaudio
import threading

class WhiteNoisePlayer:
    def __init__(self, rate=44100, chunk=1024):
        self.rate = rate
        self.chunk = chunk
        self.running = False

        try:
            self.p = pyaudio.PyAudio()
        except:
            self.p = None
        self.thread = None

    def __openSpeaker(self):
        try:
            if self.p:
                self.stream = self.p.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=self.rate,
                    output=True
                )
        except:
            self.stream = None

    def __play(self):
        try:
            while self.running:
                noise = np.random.uniform(-1, 1, self.chunk).astype(np.float32)
                if hasattr(self, 'stream') and self.stream:
                    self.stream.write(noise.tobytes())
        except:
            if hasattr(self, 'stream') and self.stream:
                self.stream.stop_stream()
                self.stream.close()

    def start(self):
        try:
            if not self.running:
                self.running = True
                self.__openSpeaker()
                self.thread = threading.Thread(target=self.__play, daemon=True)
                self.thread.start()

                return True
        except:
            return False

    def stop(self):
        try:
            self.running = False
            if self.thread:
                self.thread.join()
            if hasattr(self, 'stream') and self.stream:
                self.stream.stop_stream()
                self.stream.close()

            return True
        except:
            return False