from pathlib import Path
from vlc import MediaPlayer

class MediaController:
    def __init__(self, audio_dir="audio"):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(exist_ok=True)
        self.play_obj = None
        self.audio = None
        self.position = 0
        self.current_song = None
        self.current_artist = None

    def getlist(self):
        return [f.name for f in sorted(self.audio_dir.glob("*.mp3"))]

    def play(self, index=None):
        song = self.getlist()[index]

        if song != self.current_song:
            self.current_song = song
            self.current_artist = f"SONG-id-{index}"
            self.stop(index)
            self.audio = MediaPlayer(self.audio_dir / song)
        
        if self.audio and self.audio.is_playing():
            return

        self.audio.play()

    def pause(self, index=None):
        if self.audio:
            self.audio.pause()

    def stop(self, index=None):
        if self.audio:
            self.audio.stop()

    def upload(self, data, filename):
        path = self.audio_dir / filename
        with open(path, "wb") as f:
            f.write(data)

    def delete(self, index):
        files = self.getlist()
        if index < 0 or index >= len(files):
            return

        path = self.audio_dir / files[index]
        if path.exists():
            path.unlink()

    def read(self, index):
        files = self.getlist()
        if index < 0 or index >= len(files):
            return None
        
        return self.audio_dir / files[index]
    
    def get_current(self):
        return {
            "song": self.current_song,
            "artist": self.current_artist,
            "isPlaying": self.audio and self.audio.is_playing()
        }