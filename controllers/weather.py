import requests
import os
from functools import lru_cache
from datetime import datetime
from time import time

CACHE_TTL = 1800 # 30 mins

@lru_cache(maxsize=1)
def _get_current_weather_cached(longitude, latitude, ttl_hash):
    API_KEY = os.environ.get("OPENWEATHER_KEY")
    if not API_KEY or not ttl_hash:
        return None

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={API_KEY}&units=metric"

    res = requests.get(url)
    data = parse_current(res.json())
    data["wind"].update(get_air_quality(latitude, longitude, API_KEY))

    return data

def parse_current(data):
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]

    sunrise = datetime.fromtimestamp(data["sys"]["sunrise"])
    sunset = datetime.fromtimestamp(data["sys"]["sunset"])
    now = datetime.fromtimestamp(data["dt"])

    is_day = sunrise <= now < sunset

    rain_1h = data.get("rain", {}).get("1h", 0)

    return {
        "temp": temp,
        "temp_min": data["main"]["temp_min"],
        "temp_max": data["main"]["temp_max"],
        "feels_like": feels_like,
        "humidity": humidity,
        "pressure": pressure,
        "status": data["weather"][0]["main"],
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
        "is_day": is_day,
        "visibility": data["visibility"],
        "rain_1h": rain_1h,
        "wind": data["wind"],
        "sunrise": sunrise.isoformat(),
        "sunset": sunset.isoformat()
    }

def get_air_quality(lat, lon, key):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={key}"
    data = requests.get(url).json()

    return {
        "aqi": data["list"][0]["main"]["aqi"],
        "pm2_5": data["list"][0]["components"]["pm2_5"],
        "pm10": data["list"][0]["components"]["pm10"]
    }

def get_current_weather(longitude, latitude):
    try:
        return _get_current_weather_cached(longitude, latitude, int(time() // CACHE_TTL))
    except:
        return None