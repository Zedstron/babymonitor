from pathlib import Path
from vlc import MediaPlayer, EventType
from time import sleep

class MediaController:
    def __init__(self, audio_dir="media/audio"):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(exist_ok=True)
        self.play_obj = None
        self.audio = None
        self.position = 0
        self.current_song = None
        self.current_artist = None
        self.__loop = False
        self.audio: MediaPlayer = None
        self.handler = None
    
    def __on_position_changed(self, event):
        if self.handler and event:
            self.handler({
                "position": self.audio.get_time()
            })

    def __on_end_reached(self, event):
        if self.__loop and event:
            self.audio.stop()
            self.audio.play()

    def getlist(self):
        return [f.name for f in sorted(self.audio_dir.glob("*.mp3"))]

    def loop(self, flag):
        self.__loop = flag
    
    def volume(self, volume):
        if self.audio:
            self.audio.audio_set_volume(volume)

    def get_volume(self):
        if self.audio:
            return self.audio.audio_get_volume()
        
        return 0
    
    def mute(self, flag):
        if self.audio:
            self.audio.audio_set_mute(flag)

    def get_mute(self):
        if self.audio:
            return self.audio.audio_get_mute()
        
        return False


    def play(self, index=None, event=None):
        song = self.getlist()[index]

        if song != self.current_song:
            self.current_song = song
            self.current_artist = f"SONG-id-{index}"
            self.stop(index)
            self.audio = MediaPlayer(self.audio_dir / song)
            self.em = self.audio.event_manager()
            self.em.event_attach(EventType.MediaPlayerPositionChanged, self.__on_position_changed)
            self.em.event_attach(EventType.MediaPlayerEndReached, self.__on_end_reached)
            self.handler = event
        
        if self.audio and self.audio.is_playing():
            return

        self.audio.play()
        sleep(1)

        return { 
            "length": self.audio.get_length(),
            "volume": self.get_volume(),
            "loop": self.__loop,
            "mute": self.get_mute()
        }


    def pause(self, index=None):
        if self.audio:
            self.audio.pause()

    def stop(self, index=None):
        if self.audio:
            self.audio.stop()
    
    def seek(self, position):
        if self.audio:
            self.audio.set_position(position / 100)

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
            "isPlaying": self.audio and self.audio.is_playing(),
            "length": self.audio.get_length() if self.audio else 0,
            "volume": self.get_volume(),
            "loop": self.__loop,
            "mute": self.get_mute()
        }