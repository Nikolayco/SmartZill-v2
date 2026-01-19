#!/usr/bin/env python3
"""
NikolayCo SmartZill v2.0
Ana uygulama giriş noktası

Özellikler:
- Smart Start: Mola saatindeyse müzik otomatik başlar
- Çapraz platform: Windows, Linux, macOS
- Otomatik başlatma desteği
"""
import sys
import os
import time
import threading
import webbrowser
import platform
from pathlib import Path
from datetime import datetime

# Proje kök dizinini path'e ekle
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from config import load_config, save_config, WEB_HOST, WEB_PORT, MUSIC_DIR


def print_banner():
    """Başlangıç banner'ı"""
    print("\n" + "=" * 50)
    print("  🔔 NikolayCo SmartZill v2.0")
    print("=" * 50)
    print(f"  📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"  🖥️  {platform.system()} {platform.release()}")
    print(f"  🌐 http://localhost:{WEB_PORT}")
    print("=" * 50 + "\n")


def setup_autostart():
    """Otomatik başlatmayı ayarlar"""
    config = load_config()
    if not config.get("startup", {}).get("auto_start", True):
        return
    
    system = platform.system()
    app_path = str(PROJECT_ROOT / "smartzill.py")
    
    try:
        if system == "Linux":
            # Linux: .desktop dosyası
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = autostart_dir / "smartzill.desktop"
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=NikolayCo SmartZill
Comment=Akıllı Zil ve Anons Sistemi
Exec=python3 {app_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Terminal=false
"""
            desktop_file.write_text(desktop_content)
            print("✅ Linux otomatik başlatma ayarlandı")
            
        elif system == "Windows":
            # Windows: Registry veya Startup klasörü
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "SmartZill", 0, winreg.REG_SZ, f'pythonw "{app_path}"')
            winreg.CloseKey(key)
            print("✅ Windows otomatik başlatma ayarlandı")
            
        elif system == "Darwin":
            # macOS: LaunchAgent
            launch_agents = Path.home() / "Library" / "LaunchAgents"
            launch_agents.mkdir(parents=True, exist_ok=True)
            
            plist_file = launch_agents / "com.nikolayco.smartzill.plist"
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nikolayco.smartzill</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
            plist_file.write_text(plist_content)
            print("✅ macOS otomatik başlatma ayarlandı")
            
    except Exception as e:
        print(f"⚠️ Otomatik başlatma ayarlanamadı: {e}")


def remove_autostart():
    """Otomatik başlatmayı kaldırır"""
    system = platform.system()
    
    try:
        if system == "Linux":
            desktop_file = Path.home() / ".config" / "autostart" / "smartzill.desktop"
            if desktop_file.exists():
                desktop_file.unlink()
                
        elif system == "Windows":
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            try:
                winreg.DeleteValue(key, "SmartZill")
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
            
        elif system == "Darwin":
            plist_file = Path.home() / "Library" / "LaunchAgents" / "com.nikolayco.smartzill.plist"
            if plist_file.exists():
                plist_file.unlink()
                
    except Exception:
        pass


def smart_start():
    """
    Akıllı başlatma: Mevcut saate göre etkinlik kontrolü yapar
    YENİ MANTIK: Müzik sadece etkinlik bitişinde playMusic=true ise başlar
    """
    from core.scheduler import scheduler
    from core.audio_engine import audio_engine
    from core.media_player import media_player
    from services.holidays import holiday_service
    
    # Tatil günü ise bilgi ver
    if holiday_service.is_holiday_today():
        print("📅 Bugün tatil")
        return
    
    # Manuel player aktifse bilgi ver
    if media_player.is_playing():
        print("🎧 Manuel player aktif")
        return
    
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    day_of_week = now.weekday()
    
    # Bugünün programını al
    schedule = scheduler.get_schedule()
    today_schedule = None
    
    for day in schedule:
        if day.get("dayOfWeek") == day_of_week:
            today_schedule = day
            break
    
    if not today_schedule or not today_schedule.get("enabled"):
        print("📅 Bugün için program yok - müzik başlatılmadı")
        return
    
    # Şu an bir etkinlik içinde mi kontrol et
    in_activity = False
    for activity in today_schedule.get("activities", []):
        start_time = activity.get("startTime", "")
        end_time = activity.get("endTime", "")
        
        if start_time <= current_time < end_time:
            in_activity = True
            print(f"⏰ Etkinlik içinde: {activity.get('name', 'Bilinmeyen')} ({start_time} - {end_time})")
            print("🔇 Müzik başlatılmadı (etkinlik sırasında)")
            break
    
    # Etkinlik dışında - müzik başlatma (sadece etkinlik bitişinde playMusic kontrolü ile başlar)
    if not in_activity:
        # Son biten etkinliği bul
        last_ended = None
        for activity in sorted(today_schedule.get("activities", []), key=lambda x: x.get("endTime", ""), reverse=True):
            if activity.get("endTime", "") <= current_time:
                last_ended = activity
                break
        
        if last_ended and last_ended.get("playMusic", False):
            print(f"🎵 Mola müziği aktif olmalı ({last_ended.get('name')} sonrası)")
        else:
            print("📋 Etkinlik dışı - müzik başlatılmadı (son etkinlikten talep yok)")


def open_browser():
    """Tarayıcıyı açar"""
    config = load_config()
    if config.get("startup", {}).get("open_browser", True):
        time.sleep(3)  # Sunucunun başlamasını bekle (User request: 3s delay)
        webbrowser.open(f"http://localhost:{WEB_PORT}")


def play_startup_sound():
    """Başlangıç sesini çalar"""
    config = load_config()
    if not config.get("startup", {}).get("play_startup_sound", True):
        return
    
    from core.audio_engine import audio_engine
    from config import SOUNDS_DIR
    
    # system_audio dizininden başlangıç sesini çal
    startup_sound = SOUNDS_DIR / "system_audio" / "start.mp3"
    if startup_sound.exists():
        audio_engine.play_bell(str(startup_sound), blocking=False)


def run_server():
    """Web sunucusunu başlatır"""
    from web.server import app
    import uvicorn
    
    uvicorn.run(
        app, 
        host=WEB_HOST, 
        port=WEB_PORT, 
        log_level="warning",
        access_log=False
    )


def main():
    """Ana fonksiyon"""
    print_banner()
    
    # Yapılandırma kontrol
    config = load_config()
    
    # Otomatik başlatma ayarla
    if config.get("startup", {}).get("auto_start", True):
        setup_autostart()
    else:
        remove_autostart()
    
    # Gerekli modülleri yükle
    print("🔧 Modüller yükleniyor...")
    
    try:
        from core.audio_engine import audio_engine
        from core.media_player import media_player
        from core.scheduler import scheduler
        from services.holidays import holiday_service
        from services.birthdays import birthday_service
        print("✅ Tüm modüller yüklendi")
    except Exception as e:
        print(f"❌ Modül yükleme hatası: {e}")
        sys.exit(1)
    
    # Smart Start - mola kontrolü
    print("\n🧠 Smart Start kontrol ediliyor...")
    smart_start()
    
    # Başlangıç sesi
    play_startup_sound()
    
    # Tarayıcıyı aç (ayrı thread)
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Web sunucusunu başlat
    print(f"\n🌐 Web sunucu başlatılıyor: http://localhost:{WEB_PORT}")
    
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n👋 SmartZill kapatılıyor...")
        audio_engine.stop_all()
        media_player.stop()
        scheduler.stop()
        print("✅ Güle güle!")


if __name__ == "__main__":
    main()
