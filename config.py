"""
NikolayCo SmartZill v2.0 - Yapılandırma Modülü
"""
import os
import json
from pathlib import Path

# Temel dizinler
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
SOUNDS_DIR = BASE_DIR / "sounds"

# Ses dizinleri
BELLS_DIR = SOUNDS_DIR / "bells"
ANNOUNCEMENTS_DIR = SOUNDS_DIR / "announcements"
MUSIC_DIR = SOUNDS_DIR / "music"
SYSTEM_DIR = SOUNDS_DIR / "system"

# Veri dosyaları
CONFIG_FILE = DATA_DIR / "config.json"
SCHEDULE_FILE = DATA_DIR / "schedule.json"
SPECIAL_DAYS_FILE = DATA_DIR / "special_days.json"

# Web sunucu ayarları
WEB_HOST = "0.0.0.0"
WEB_PORT = 7777

# Streaming ayarları
STREAM_PORT = 5959
STREAM_BITRATE = 128

# Varsayılan yapılandırma
DEFAULT_CONFIG = {
    "company_name": "NikolayCo SmartZill",
    "language": "tr",
    "theme": "dark",
    "volumes": {
        "bell": 100,
        "announcement": 80,
        "music": 60,
        "manual": 70
    },
    "tts": {
        "engine": "edge",
        "voice": "tr-TR-AhmetNeural",
        "rate": "+0%"
    },
    "radio": {
        "enabled": False,
        "url": "",
        "stations": []
    },
    "streaming": {
        "enabled": False,
        "port": STREAM_PORT,
        "bitrate": STREAM_BITRATE
    },
    "holidays": {
        "enabled": True,
        "country": "TR",
        "skip_on_holidays": True
    },
    "startup": {
        "auto_start": True,
        "open_browser": True,
        "play_startup_sound": True
    },
    "security": {
        "admin_password": "admin"  # Change this in the settings interface or config.json
    }
}


def ensure_directories():
    """Gerekli dizinleri oluşturur"""
    for dir_path in [DATA_DIR, BELLS_DIR, ANNOUNCEMENTS_DIR, MUSIC_DIR, SYSTEM_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Yapılandırmayı yükler, yoksa varsayılanı oluşturur"""
    ensure_directories()
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Eksik anahtarları varsayılandan doldur
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception:
            pass
    
    # Varsayılan yapılandırmayı kaydet
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Yapılandırmayı kaydeder"""
    ensure_directories()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def load_schedule() -> list:
    """Haftalık programı yükler"""
    ensure_directories()
    
    if SCHEDULE_FILE.exists():
        try:
            with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    
    # Varsayılan boş program
    return get_default_schedule()


def save_schedule(schedule: list):
    """Haftalık programı kaydeder"""
    ensure_directories()
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)


def get_default_schedule() -> list:
    """Varsayılan 7 günlük program şablonu"""
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    schedule = []
    
    for i, day_name in enumerate(days):
        schedule.append({
            "dayOfWeek": i,
            "dayName": day_name,
            "enabled": i < 5,  # Hafta içi aktif
            "activities": []
        })
    
    return schedule


# Uygulama başlatıldığında dizinleri oluştur
ensure_directories()
