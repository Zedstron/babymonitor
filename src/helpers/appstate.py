from time import time
from helpers.logger import logger
from aiortc import RTCPeerConnection
from typing import Dict, List, Optional
from helpers.utils import quick_speed_test
from aiortc.contrib.media import MediaRecorder
from helpers.database import get_settings, save_settings, get_profile

class AppState:
    def __init__(self, volume):
        self.pcs: dict[str, RTCPeerConnection] = dict()
        self.recorder: MediaRecorder = None
        self.recorder_task = None

        self.connected_clients: Dict[str, dict] = {}

        self.sensor_data = {
            "temperature": 24.5,
            "humidity": 58,
            "noise": 32,
            "occupancy": 1,
            "confidence": "98%"
        }

        self.settings = get_settings({
            "baby_name": "Cookie",
            "cry_detection": False,
            "led_indicator": True,
            "buzzer_enabled": False,
            "video_quality": "high",
            "video_resolution": "1080",
            "video_fps": "30",
            "latitude": 33.69186440015098, 
            "longitude": 72.82942605084591
        })

        self.notifications: List[dict] = []
        self.max_notifications = 50

        self.is_recording = False
        self.recording_start_time: Optional[float] = None
        self.current_recording_path: Optional[str] = None

        self.audio_listen_enabled = True
        self.current_volume = volume
        
        self.start_time = time()

        try:
            logger.info("Please wait current bandwidth is being calculated")
            self.bandwidth = quick_speed_test()
        except Exception as e:
            logger.warning("Bandwidth calculation failed, skipping " + str(e))
            self.bandwidth = {
                "upload": { "speed": 0, "label": "No Connection" },
                "download": { "speed": 0, "label": "No Connection" }
            }

        self.user_profile = {
            "profile_pic": "/assets/img/zain.jpeg",
            **get_profile()
        }
    
    def save_settings(self):
        try:
            save_settings(self.settings)
        except Exception as e:
            logger.error(f"Settings save error: {e}")