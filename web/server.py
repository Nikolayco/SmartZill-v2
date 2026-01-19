"""
NikolayCo SmartZill v2.0 - Web Sunucu
FastAPI tabanlı REST API ve statik dosya sunumu
"""
import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
import json
import sys

# Proje kök dizinini path'e ekle
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    load_config, save_config, load_schedule, save_schedule,
    BELLS_DIR, ANNOUNCEMENTS_DIR, MUSIC_DIR, SOUNDS_DIR, WEB_HOST, WEB_PORT
)
from core.audio_engine import audio_engine
from core.media_player import media_player
from core.scheduler import scheduler
from core.tts_engine import tts_engine
from services.holidays import holiday_service
from services.birthdays import birthday_service
from services.backup import backup_service

# FastAPI uygulaması
app = FastAPI(title="NikolayCo SmartZill v2.0", version="2.0.0")

# CORS - yerel ağ için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Uygulama başladığında"""
    print("[Server] Başlatılıyor...")
    scheduler.start()

# Statik dosyalar
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ===== PYDANTIC MODELLER =====

class VolumeRequest(BaseModel):
    channel: str
    volume: int

class ScheduleRequest(BaseModel):
    schedule: list

class ActivityRequest(BaseModel):
    dayOfWeek: int
    activity: dict

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "tr"
    gender: Optional[str] = "female"

class RadioRequest(BaseModel):
    url: str

class PlaylistRequest(BaseModel):
    files: List[str]
    shuffle: Optional[bool] = False

class ConfigRequest(BaseModel):
    key: str
    value: Any

class PersonRequest(BaseModel):
    name: str
    date: str

class AuthRequest(BaseModel):
    password: str


# ===== TEMEL ENDPOINT'LER =====

@app.post("/api/auth/verify")
async def verify_password(req: AuthRequest):
    """Admin şifresini doğrula"""
    config = load_config()
    # Config'deki şifreyi al, yoksa varsayılanı kullan
    correct_password = config.get("security", {}).get("admin_password", "*3512488Nfs*")
    
    if req.password == correct_password:
        return {"success": True}
    
    return {"success": False}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Ana sayfa"""
    template_path = TEMPLATES_DIR / "index.html"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return "<h1>NikolayCo SmartZill v2.0</h1><p>Web arayüzü yükleniyor...</p>"


@app.get("/ads.txt")
async def get_ads_txt():
    """Google AdSense ads.txt dosyası"""
    ads_file = PROJECT_ROOT / "ads.txt"
    if ads_file.exists():
        return FileResponse(ads_file)
    return Response(content="File not found", status_code=404)


@app.get("/api/status")
async def get_status():
    """Sistem durumu"""
    config = load_config()
    return {
        "version": "2.0.0",
        "company_name": config.get("company_name", "NikolayCo SmartZill"),
        "current_time": datetime.now().strftime("%H:%M:%S"),
        "scheduler": scheduler.get_status(),
        "audio": audio_engine.get_status(),
        "media_player": media_player.get_status(),
        "holidays": {
            "is_holiday": holiday_service.is_holiday_today(),
            "holiday_name": holiday_service.get_holiday_name()
        }
    }


# ===== SES KONTROL =====

@app.post("/api/volume")
async def set_volume(req: VolumeRequest):
    """Kanal ses seviyesi ayarla"""
    if req.channel == "manual":
        media_player.set_volume(req.volume)
    else:
        audio_engine.set_volume(req.channel, req.volume)
    return {"success": True, "channel": req.channel, "volume": req.volume}


@app.get("/api/volumes")
async def get_volumes():
    """Tüm ses seviyelerini getir"""
    config = load_config()
    return config.get("volumes", {})


@app.post("/api/bell/play")
async def play_bell(filename: str = "default.mp3"):
    """Zil çal"""
    def play_async():
        audio_engine.play_bell(filename, blocking=True)
    
    import threading
    threading.Thread(target=play_async, daemon=True).start()
    return {"success": True, "playing": filename}


@app.post("/api/announcement/play")
async def play_announcement(filename: str):
    """Anons çal"""
    def play_async():
        audio_engine.play_announcement(filename, blocking=True)
    
    import threading
    threading.Thread(target=play_async, daemon=True).start()
    return {"success": True, "playing": filename}


@app.post("/api/tts")
async def generate_tts(req: TTSRequest):
    """TTS ile ses oluştur ve çal"""
    tts_engine.set_language(req.language)
    tts_engine.set_gender(req.gender)
    
    filepath = await tts_engine.generate_async(req.text)
    if filepath:
        def play_async():
            audio_engine.play_announcement(filepath, blocking=True)
        
        import threading
        threading.Thread(target=play_async, daemon=True).start()
        return {"success": True, "file": filepath}
    
    raise HTTPException(status_code=500, detail="TTS oluşturulamadı")


@app.post("/api/stop")
async def stop_all():
    """Tüm sesleri durdur"""
    audio_engine.stop_all()
    media_player.stop()
    return {"success": True}


# ===== MEDYA PLAYER =====

@app.get("/api/media/status")
async def get_media_status():
    """Medya player durumu"""
    return media_player.get_status()


@app.post("/api/media/play/file")
async def play_media_file(filename: str):
    """Dosya oynat"""
    success = media_player.play_file(filename)
    return {"success": success}


@app.post("/api/media/play/radio")
async def play_radio(req: RadioRequest):
    """Radyo oynat (YouTube dahil)"""
    success = media_player.play_radio(req.url)
    return {"success": success}


@app.post("/api/media/play/playlist")
async def play_playlist(req: PlaylistRequest):
    """Playlist oynat"""
    success = media_player.play_playlist(req.files, req.shuffle)
    return {"success": success}


@app.post("/api/media/pause")
async def toggle_media():
    """Oynat/Duraklat"""
    media_player.toggle_play_pause()
    return {"success": True, "paused": media_player.is_paused}


@app.post("/api/media/stop")
async def stop_media():
    """Medya durdur"""
    media_player.stop()
    return {"success": True}


@app.post("/api/media/next")
async def next_track():
    """Sonraki parça"""
    media_player.next_track()
    return {"success": True}


@app.post("/api/media/prev")
async def prev_track():
    """Önceki parça"""
    media_player.previous_track()
    return {"success": True}


@app.get("/api/media/files")
async def get_media_files():
    """Müzik dosyalarını listele"""
    return media_player.get_music_files()


# ===== ZAMANLAYICI =====

@app.get("/api/schedule")
async def get_schedule():
    """Haftalık programı getir"""
    return scheduler.get_schedule()


@app.post("/api/schedule")
async def update_schedule(req: ScheduleRequest):
    """Haftalık programı güncelle"""
    scheduler.update_schedule(req.schedule)
    return {"success": True}


@app.get("/api/schedule/today")
async def get_today_schedule():
    """Bugünün programını getir"""
    day_of_week = datetime.now().weekday()
    schedule = scheduler.get_schedule()
    for day in schedule:
        if day.get("dayOfWeek") == day_of_week:
            return day
    return {"activities": []}


@app.get("/api/schedule/timeline")
async def get_timeline():
    """Günlük zaman çizelgesi"""
    return scheduler.get_daily_timeline()


@app.post("/api/scheduler/start")
async def start_scheduler():
    """Zamanlayıcıyı başlat"""
    scheduler.start()
    return {"success": True, "running": True}


@app.post("/api/scheduler/stop")
async def stop_scheduler():
    """Zamanlayıcıyı geçici olarak pasif yap - tüm otomatik sesleri durdur"""
    scheduler.stop()
    # Tüm otomatik sesleri durdur
    audio_engine.stop_all()
    return {"success": True, "running": False}




@app.post("/api/schedule/activity")
async def add_activity(req: ActivityRequest):
    """Etkinlik ekle"""
    success = scheduler.add_activity(req.dayOfWeek, req.activity)
    if not success:
        raise HTTPException(status_code=400, detail="Etkinlik eklenemedi (zaman çakışması olabilir)")
    return {"success": True}


@app.delete("/api/schedule/activity/{day}/{activity_id}")
async def remove_activity(day: int, activity_id: str):
    """Etkinlik sil"""
    success = scheduler.remove_activity(day, activity_id)
    return {"success": success}


# ===== SES DOSYALARI =====

@app.get("/api/sounds/{category}")
async def list_sounds(category: str):
    """Ses dosyalarını listele"""
    dir_map = {
        "bells": BELLS_DIR,
        "announcements": ANNOUNCEMENTS_DIR,
        "music": MUSIC_DIR
    }
    
    dir_path = dir_map.get(category)
    if not dir_path or not dir_path.exists():
        return []
    
    files = []
    for f in dir_path.iterdir():
        if f.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac", ".m4a"):
            files.append({
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size
            })
    
    return sorted(files, key=lambda x: x["name"].lower())


@app.post("/api/sounds/{category}/upload")
async def upload_sound(category: str, files: List[UploadFile] = File(...)):
    """Ses dosyası yükle"""
    dir_map = {
        "bells": BELLS_DIR,
        "announcements": ANNOUNCEMENTS_DIR,
        "music": MUSIC_DIR
    }
    
    dir_path = dir_map.get(category)
    if not dir_path:
        raise HTTPException(status_code=400, detail="Geçersiz kategori")
    
    dir_path.mkdir(parents=True, exist_ok=True)
    uploaded = []
    
    for file in files:
        if file.filename:
            filepath = dir_path / file.filename
            content = await file.read()
            filepath.write_bytes(content)
            uploaded.append(file.filename)
    
    return {"success": True, "uploaded": uploaded}


@app.delete("/api/sounds/{category}/{filename}")
async def delete_sound(category: str, filename: str):
    """Ses dosyası sil"""
    dir_map = {
        "bells": BELLS_DIR,
        "announcements": ANNOUNCEMENTS_DIR,
        "music": MUSIC_DIR
    }
    
    dir_path = dir_map.get(category)
    if not dir_path:
        raise HTTPException(status_code=400, detail="Geçersiz kategori")
    
    filepath = dir_path / filename
    if filepath.exists():
        filepath.unlink()
        return {"success": True}
    
    raise HTTPException(status_code=404, detail="Dosya bulunamadı")


@app.get("/api/sounds/{category}/{filename}/preview")
async def preview_sound(category: str, filename: str):
    """Ses dosyası önizle"""
    dir_map = {
        "bells": BELLS_DIR,
        "announcements": ANNOUNCEMENTS_DIR,
        "music": MUSIC_DIR
    }
    
    dir_path = dir_map.get(category)
    if not dir_path:
        raise HTTPException(status_code=400, detail="Geçersiz kategori")
    
    filepath = dir_path / filename
    if filepath.exists():
        return FileResponse(filepath, media_type="audio/mpeg")
    
    raise HTTPException(status_code=404, detail="Dosya bulunamadı")


# ===== TATİLLER =====

@app.get("/api/holidays")
async def get_holidays():
    """Tatil durumu"""
    return holiday_service.get_status()


@app.post("/api/holidays/country")
async def set_holiday_country(country: str):
    """Ülke değiştir"""
    holiday_service.set_country(country)
    return {"success": True, "country": country}


@app.post("/api/holidays/enabled")
async def set_holidays_enabled(enabled: bool):
    """Tatil kontrolü aç/kapat"""
    holiday_service.set_enabled(enabled)
    return {"success": True, "enabled": enabled}


@app.post("/api/holidays/mute")
async def set_holiday_muted(date: str, muted: bool):
    """Belirli bir tatili sessize al/aktif et"""
    holiday_service.set_holiday_muted(date, muted)
    return {"success": True, "date": date, "muted": muted}



# ===== DOĞUM GÜNLERİ =====

@app.get("/api/birthdays")
async def get_birthdays():
    """Doğum günü durumu"""
    return birthday_service.get_status()


@app.get("/api/birthdays/people")
async def get_people():
    """Tüm kişiler"""
    return birthday_service.get_all_people()


@app.post("/api/birthdays/person")
async def add_person(req: PersonRequest):
    """Kişi ekle"""
    success = birthday_service.add_person(req.name, req.date)
    return {"success": success}


@app.delete("/api/birthdays/person/{name}")
async def remove_person(name: str):
    """Kişi sil"""
    success = birthday_service.remove_person(name)
    return {"success": success}


class AnnouncementTimesRequest(BaseModel):
    times: List[str]


@app.post("/api/birthdays/times")
async def set_announcement_times(req: AnnouncementTimesRequest):
    """Anons saatlerini ayarla"""
    birthday_service.set_announcement_times(req.times)
    return {"success": True, "times": req.times}


@app.post("/api/birthdays/import")
async def import_birthdays(file: UploadFile = File(...)):
    """Excel/CSV'den içe aktar"""
    content = await file.read()
    
    if file.filename.endswith(".csv"):
        count = birthday_service.import_from_csv(content.decode("utf-8"))
    else:
        # Excel için geçici dosya
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        count = birthday_service.import_from_excel(tmp_path)
        os.unlink(tmp_path)
    
    return {"success": True, "imported": count}


@app.get("/api/birthdays/template")
async def download_birthday_template():
    """Doğum günü şablonunu indir"""
    try:
        import openpyxl
        from io import BytesIO
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Doğum Günleri"
        
        # Başlıklar
        ws.append(["Ad Soyad", "Doğum Tarihi (GG.AA.YYYY)"])
        
        # Örnek veri
        ws.append(["Ahmet Yılmaz", "01.01.1990"])
        ws.append(["Ayşe Demir", "15.05.1985"])
        
        # Sütun genişlikleri
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        headers = {
            'Content-Disposition': 'attachment; filename="Dogum_Gunu_Sablonu.xlsx"'
        }
        
        # FileResponse yerine doğrudan Response dönebiliriz streaming ile veya content ile
        return Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Şablon oluşturulamadı: {str(e)}")


class TemplateRequest(BaseModel):
    template: str


@app.post("/api/birthdays/template")
async def set_birthday_template(req: TemplateRequest):
    """Doğum günü anons şablonunu ayarla"""
    birthday_service.set_template(req.template)
    return {"success": True, "template": req.template}


# ===== YEDEKLEME =====

@app.get("/api/backup/list")
async def list_backups():
    """Yedekleri listele"""
    return backup_service.get_backup_list()


@app.get("/api/backup/export/json")
async def export_json():
    """JSON olarak dışa aktar"""
    data = backup_service.export_to_bytes("json")
    filename = f"NikolayCo_SmartZill_Yedek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/backup/export/excel")
async def export_excel():
    """Excel olarak dışa aktar"""
    data = backup_service.export_to_bytes("excel")
    filename = f"NikolayCo_SmartZill_Yedek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/backup/import")
async def import_backup(file: UploadFile = File(...)):
    """Yedeği içe aktar"""
    content = await file.read()
    
    import tempfile
    suffix = ".json" if file.filename.endswith(".json") else ".xlsx"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    if suffix == ".json":
        success = backup_service.restore_from_json(tmp_path)
    else:
        success = backup_service.restore_from_excel(tmp_path)
    
    os.unlink(tmp_path)
    
    if success:
        return {"success": True}
    raise HTTPException(status_code=500, detail="Yedek geri yüklenemedi")


# ===== AYARLAR =====

@app.get("/api/config")
async def get_config():
    """Tüm ayarları getir"""
    return load_config()


@app.post("/api/config")
async def update_config(config: dict):
    """Ayarları güncelle"""
    save_config(config)
    return {"success": True}


@app.get("/api/tts/voices")
async def get_tts_voices():
    """Mevcut TTS sesleri"""
    return tts_engine.get_available_voices()


# ===== YAŞAM DÖNGÜSÜ =====

@app.on_event("startup")
async def startup():
    """Uygulama başlangıcı"""
    print("=" * 50)
    print("  NikolayCo SmartZill v2.0")
    print(f"  http://{WEB_HOST}:{WEB_PORT}")
    print("=" * 50)
    
    # Zamanlayıcıyı başlat
    scheduler.on_bell = lambda f: audio_engine.play_bell(f, blocking=True)
    scheduler.on_announcement = lambda f: audio_engine.play_announcement(f, blocking=True)
    scheduler.on_music_start = lambda: _start_break_music()
    scheduler.on_music_stop = lambda: audio_engine.stop_music()
    scheduler.holiday_checker = holiday_service.is_holiday_today
    scheduler.is_manual_player_active = lambda: media_player.is_playing()
    scheduler.birthday_checker = birthday_service.should_announce_now
    scheduler.start()


def _start_break_music():
    """Mola müziğini başlat (radyo veya yerel)"""
    config = load_config()
    radio_config = config.get("radio", {})
    
    if radio_config.get("enabled") and radio_config.get("url"):
        # Radyo dene
        if audio_engine.play_music(radio_config["url"], is_stream=True):
            return
    
    # Yerel müziklere geç
    music_files = [f.name for f in MUSIC_DIR.iterdir() 
                   if f.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac", ".m4a")]
    
    if music_files:
        import random
        random.shuffle(music_files)
        audio_engine.play_music(music_files[0])


# ===== SYSTEM CONTROL =====

@app.post("/api/system/restart")
async def restart_system():
    """Uygulamayı yeniden başlat"""
    import os
    import sys
    
    def restart():
        import time
        time.sleep(1)
        scheduler.stop()
        audio_engine.stop_all()
        media_player.stop()
        
        # Python'u yeniden başlat
        os.execv(sys.executable, ['python'] + sys.argv)
    
    import threading
    threading.Thread(target=restart, daemon=True).start()
    return {"success": True, "message": "Yeniden başlatılıyor..."}


@app.post("/api/system/shutdown")
async def shutdown_system():
    """Uygulamayı tamamen kapat"""
    def shutdown():
        import time
        time.sleep(1)
        scheduler.stop()
        audio_engine.stop_all()
        media_player.stop()
        print("SmartZill kapatılıyor...")
        os._exit(0)
    
    import threading
    threading.Thread(target=shutdown, daemon=True).start()
    return {"success": True, "message": "Kapatılıyor..."}


@app.on_event("shutdown")
async def shutdown():
    """Uygulama kapanışı"""
    scheduler.stop()
    audio_engine.stop_all()
    media_player.stop()
    print("SmartZill kapatıldı.")


def run_server():
    """Sunucuyu başlat"""
    import uvicorn
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT, log_level="warning")


if __name__ == "__main__":
    run_server()
