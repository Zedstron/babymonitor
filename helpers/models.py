from pydantic import BaseModel
from typing import Optional

class SettingsUpdate(BaseModel):
    baby_name: Optional[str] = None
    cry_detection: Optional[bool] = None
    led_indicator: Optional[bool] = None
    buzzer_enabled: Optional[bool] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None

class VideoSettings(BaseModel):
    resolution: Optional[str] = None
    quality: Optional[str] = None
    fps: Optional[str] = None

class AudioControl(BaseModel):
    enabled: bool

class PTTData(BaseModel):
    timestamp: int

class LullabyPlay(BaseModel):
    song_id: str