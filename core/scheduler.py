"""
NikolayCo SmartZill v2.0 - Zamanlayıcı Servisi
7 günlük haftalık program yönetimi
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import load_config, load_schedule, save_schedule


class SchedulerService:
    """
    7 günlük zamanlayıcı servisi
    
    Etkinlik türleri:
    - shift_start: Vardiya başlangıç
    - shift_end: Vardiya bitiş
    - break_start: Mola başlangıç
    - break_end: Mola bitiş
    - custom: Özel etkinlik
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Program
        self.schedule = load_schedule()
        
        # Durum
        self.current_state = "idle"  # idle, in_activity
        self.next_event: Optional[dict] = None
        self.last_triggered_event: Optional[str] = None
        self.background_music_playing = False
        self.in_activity = False
        self.current_activity: Optional[dict] = None  # Şu anki aktif etkinlik
        self.last_ended_activity: Optional[dict] = None  # Son biten etkinlik
        self.announced_birthdays: set = set()  # Bugün anons edilen doğum günleri
        
        # Callback'ler
        self.on_bell: Optional[callable] = None
        self.on_announcement: Optional[callable] = None
        self.on_music_start: Optional[callable] = None
        self.on_music_stop: Optional[callable] = None
        self.is_manual_player_active: Optional[callable] = None  # Manuel player kontrolü
        self.birthday_checker: Optional[callable] = None  # Doğum günü kontrolü
        
        # Tatil kontrolü
        self.holiday_checker: Optional[callable] = None
    
    def start(self):
        """Zamanlayıcıyı başlatır"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[Scheduler] Başlatıldı")
        
        # Başlangıçta mevcut durumu kontrol et ve gerekirse müziği başlat
        self._check_initial_state()
    
    def stop(self):
        """Zamanlayıcıyı durdurur"""
        self.running = False
        self.background_music_playing = False  # Durdurulduğunda müzik durumunu sıfırla
        if self.thread:
            self.thread.join(timeout=2)
        print("[Scheduler] Durduruldu")
    
    def _loop(self):
        """Ana zamanlayıcı döngüsü"""
        while self.running:
            try:
                self._tick()
            except Exception as e:
                print(f"[Scheduler] Hata: {e}")
            
            time.sleep(1)
    
    def _tick(self):
        """Her saniye çalışır"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        day_of_week = now.weekday()
        
        # Bugünün programını al
        today_schedule = self._get_day_schedule(day_of_week)
        
        if not today_schedule or not today_schedule.get("enabled", True):
            self._update_next_event(None)
            self._stop_background_music()
            return
        
        # Tatil kontrolü
        if self.holiday_checker and self.holiday_checker():
            self._update_next_event(None)
            self._stop_background_music()
            return
        
        # Etkinlikleri kontrol et
        activities = today_schedule.get("activities", [])
        
        for activity in activities:
            activity_id = activity.get("id", "")
            
            # Başlangıç zamanı
            start_time = activity.get("startTime", "")
            if start_time == current_time:
                event_key = f"{activity_id}_start_{now.strftime('%Y%m%d')}"
                if self.last_triggered_event != event_key:
                    self.last_triggered_event = event_key
                    self._trigger_activity_start(activity)
            
            # Bitiş zamanı
            end_time = activity.get("endTime", "")
            if end_time == current_time:
                event_key = f"{activity_id}_end_{now.strftime('%Y%m%d')}"
                if self.last_triggered_event != event_key:
                    self.last_triggered_event = event_key
                    self._trigger_activity_end(activity)
            
            # Ara anonslar
            for interim in activity.get("interimAnnouncements", []):
                if interim.get("enabled") and interim.get("time") == current_time:
                    interim_key = f"{interim.get('id', '')}_interim_{now.strftime('%Y%m%d')}"
                    if self.last_triggered_event != interim_key:
                        self.last_triggered_event = interim_key
                        self._trigger_interim(interim)
        
        # Doğum günü kontrolü
        if self.birthday_checker:
            birthday_names = self.birthday_checker()
            if birthday_names:
                # Her kişi için ayrı anons yap
                for name in birthday_names:
                    birthday_key = f"birthday_{name}_{now.strftime('%Y%m%d_%H%M')}"
                    # Bu kişi bu saat için daha önce anons edilmemiş mi kontrol et
                    if birthday_key not in self.announced_birthdays:
                        self.announced_birthdays.add(birthday_key)
                        self._trigger_birthday(name)
                        
                # Gün değiştiğinde seti temizle
                if now.strftime('%H:%M') == '00:00':
                    self.announced_birthdays.clear()
        
        # Sonraki etkinliği güncelle
        self._update_next_event(self._find_next_event(activities, current_time))
        
        # Etkinlik içinde mi kontrol et ve müzik durumunu yönet
        self._manage_background_music(activities, current_time)
    
    def _trigger_activity_start(self, activity: dict):
        """Etkinlik başlangıcını tetikler"""
        print(f"[Scheduler] Etkinlik başladı: {activity.get('name', 'Bilinmeyen')}")
        
        # Etkinlik içine girdik - müziği durdur (etkinlik sırasında çalışma var, müzik yok)
        self.in_activity = True
        self.current_activity = activity  # Aktif etkinliği sakla
        self._stop_background_music()
        
        # Başlangıç zili
        bell_id = activity.get("startSoundId")
        bell_played = False
        if bell_id and self.on_bell:
            self.on_bell(bell_id)
            bell_played = True
        
        # Başlangıç anonsu
        announcement_id = activity.get("startAnnouncementId")
        if announcement_id and self.on_announcement:
            # Zil çaldıysa 2 saniye bekle
            if bell_played:
                time.sleep(2)
            self.on_announcement(announcement_id)
        
        self.current_state = "in_activity"
    
    def _trigger_activity_end(self, activity: dict):
        """Etkinlik bitişini tetikler"""
        print(f"[Scheduler] Etkinlik bitti: {activity.get('name', 'Bilinmeyen')}")
        
        # Bitiş zili
        bell_id = activity.get("endSoundId")
        bell_played = False
        if bell_id and self.on_bell:
            self.on_bell(bell_id)
            bell_played = True
        
        # Bitiş anonsu
        announcement_id = activity.get("endAnnouncementId")
        if announcement_id and self.on_announcement:
            # Zil çaldıysa 2 saniye bekle
            if bell_played:
                time.sleep(2)
            self.on_announcement(announcement_id)
        
        # Etkinlik bitti - sadece playMusic=true ise müziği başlat
        self.in_activity = False
        self.current_state = "idle"
        self.current_activity = None
        self.last_ended_activity = activity  # Son biten etkinliği sakla
        
        # Sadece bu etkinliğin playMusic ayarı açıksa müziği başlat
        if activity.get("playMusic", False):
            print(f"[Scheduler] Etkinlik sonrası müzik başlatılıyor (playMusic=true)")
            self._start_background_music()
        else:
            print(f"[Scheduler] Etkinlik sonrası müzik başlatılmıyor (playMusic=false)")
    
    def _trigger_interim(self, interim: dict):
        """Ara anonsu tetikler"""
        print(f"[Scheduler] Ara anons çalıyor")
        sound_id = interim.get("soundId")
        if sound_id and self.on_announcement:
            self.on_announcement(sound_id)
    
    def _trigger_birthday(self, name: str):
        """Doğum günü anonsu tetikler"""
        print(f"[Scheduler] Doğum günü anonsu: {name}")
        
        # TTS ile doğum günü anonsu oluştur
        try:
            from core.tts_engine import tts_engine
            from services.birthdays import birthday_service
            
            # Şablonu al
            template = birthday_service.get_announcement_text(name)
            
            # TTS dosyası oluştur
            filepath = tts_engine.generate(template, f"birthday_{name.replace(' ', '_')}.mp3")
            
            if filepath and self.on_announcement:
                self.on_announcement(filepath)
        except Exception as e:
            print(f"[Scheduler] Doğum günü anonsu hatası: {e}")
    
    def _manage_background_music(self, activities: list, current_time: str):
        """Arka plan müziğini yönetir - etkinlik sonrası molada çalar"""
        # Manuel player aktifse dokunma
        if self.is_manual_player_active and self.is_manual_player_active():
            return
        
        # Herhangi bir etkinlik içinde miyiz?
        in_any_activity = False
        
        for activity in activities:
            start = activity.get("startTime", "")
            end = activity.get("endTime", "")
            
            if start <= current_time < end:
                in_any_activity = True
                break
        
        # Etkinlik içindeyse müziği durdur
        if in_any_activity:
            if self.background_music_playing:
                self._stop_background_music()
        else:
            # Etkinlik dışında (mola) - en son biten etkinliği bul
            # Eğer last_ended_activity yoksa, şu anki zamandan önce biten son etkinliği bul
            if not self.last_ended_activity:
                for activity in sorted(activities, key=lambda x: x.get("endTime", ""), reverse=True):
                    if activity.get("endTime", "") <= current_time:
                        self.last_ended_activity = activity
                        break
            
            # Son biten etkinliğin playMusic ayarını kontrol et
            if self.last_ended_activity and self.last_ended_activity.get("playMusic", False):
                # playMusic=true ise müzik çalmalı
                if not self.background_music_playing:
                    print("[Scheduler] Mola sırasında müzik başlatılıyor (son etkinlik playMusic=true)")
                    self._start_background_music()
            else:
                # playMusic=false veya hiç etkinlik bitmediyse müzik çalmamalı
                if self.background_music_playing:
                    self._stop_background_music()
    
    def _start_background_music(self):
        """Arka plan müziğini başlatır"""
        if self.background_music_playing:
            return
        
        # Manuel player aktifse dokunma
        if self.is_manual_player_active and self.is_manual_player_active():
            return
        
        print("[Scheduler] Arka plan müziği başlatılıyor")
        if self.on_music_start:
            self.on_music_start()
            self.background_music_playing = True
    
    def _stop_background_music(self):
        """Arka plan müziğini durdurur"""
        if not self.background_music_playing:
            return
        
        print("[Scheduler] Arka plan müziği durduruluyor")
        if self.on_music_stop:
            self.on_music_stop()
            self.background_music_playing = False
    
    def _find_next_event(self, activities: list, current_time: str) -> Optional[dict]:
        """Sonraki etkinliği bulur"""
        next_event = None
        next_time = None
        
        for activity in activities:
            for time_key in ["startTime", "endTime"]:
                event_time = activity.get(time_key, "")
                
                if event_time > current_time:
                    if next_time is None or event_time < next_time:
                        next_time = event_time
                        next_event = {
                            "time": event_time,
                            "name": activity.get("name", ""),
                            "type": "start" if time_key == "startTime" else "end"
                        }
        
        return next_event
    
    def _update_next_event(self, event: Optional[dict]):
        """Sonraki etkinliği günceller"""
        with self.lock:
            self.next_event = event
    
    def _get_day_schedule(self, day_of_week: int) -> Optional[dict]:
        """Belirli günün programını döndürür"""
        for day in self.schedule:
            if day.get("dayOfWeek") == day_of_week:
                return day
        return None
    
    def get_schedule(self) -> list:
        """Tam programı döndürür"""
        return self.schedule
    
    def update_schedule(self, new_schedule: list):
        """Programı günceller"""
        with self.lock:
            self.schedule = new_schedule
            save_schedule(new_schedule)
        print("[Scheduler] Program güncellendi")
    
    def update_day(self, day_of_week: int, day_data: dict):
        """Tek günü günceller"""
        with self.lock:
            for i, day in enumerate(self.schedule):
                if day.get("dayOfWeek") == day_of_week:
                    self.schedule[i] = day_data
                    break
            else:
                self.schedule.append(day_data)
            
            save_schedule(self.schedule)
    
    def add_activity(self, day_of_week: int, activity: dict) -> bool:
        """Etkinlik ekler, çakışma kontrolü yapar"""
        day = self._get_day_schedule(day_of_week)
        if not day:
            return False
        
        # Çakışma kontrolü
        new_start = activity.get("startTime", "")
        new_end = activity.get("endTime", "")
        
        for existing in day.get("activities", []):
            ex_start = existing.get("startTime", "")
            ex_end = existing.get("endTime", "")
            
            # Zaman çakışması
            if (new_start < ex_end and new_end > ex_start):
                return False
        
        # Etkinliği ekle
        with self.lock:
            for d in self.schedule:
                if d.get("dayOfWeek") == day_of_week:
                    if "activities" not in d:
                        d["activities"] = []
                    d["activities"].append(activity)
                    d["activities"].sort(key=lambda x: x.get("startTime", ""))
                    break
            
            save_schedule(self.schedule)
        
        return True
    
    def remove_activity(self, day_of_week: int, activity_id: str) -> bool:
        """Etkinlik siler"""
        with self.lock:
            for day in self.schedule:
                if day.get("dayOfWeek") == day_of_week:
                    activities = day.get("activities", [])
                    day["activities"] = [a for a in activities if a.get("id") != activity_id]
                    save_schedule(self.schedule)
                    return True
        return False
    
    def get_status(self) -> dict:
        """Zamanlayıcı durumunu döndürür"""
        with self.lock:
            return {
                "running": self.running,
                "state": self.current_state,
                "next_event": self.next_event,
                "current_time": datetime.now().strftime("%H:%M:%S"),
                "day_of_week": datetime.now().weekday()
            }
    
    def get_daily_timeline(self) -> list:
        """Bugünün zaman çizelgesini döndürür"""
        day_of_week = datetime.now().weekday()
        day = self._get_day_schedule(day_of_week)
        
        if not day:
            return []
        
        timeline = []
        
        for activity in day.get("activities", []):
            timeline.append({
                "time": activity.get("startTime", ""),
                "name": activity.get("name", ""),
                "type": "start",
                "activity_type": activity.get("type", "custom")
            })
            timeline.append({
                "time": activity.get("endTime", ""),
                "name": activity.get("name", ""),
                "type": "end",
                "activity_type": activity.get("type", "custom")
            })
        
        return sorted(timeline, key=lambda x: x["time"])
    
    def _check_initial_state(self):
        """Uygulama başlangıcında mevcut durumu kontrol eder ve müziği başlatır"""
        import time
        time.sleep(1)  # Diğer servislerin başlaması için kısa bir bekleme
        
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        day_of_week = now.weekday()
        
        # Bugünün programını al
        today_schedule = self._get_day_schedule(day_of_week)
        
        if not today_schedule or not today_schedule.get("enabled", True):
            return
        
        # Tatil kontrolü
        if self.holiday_checker and self.holiday_checker():
            return
        
        # Manuel player aktifse dokunma
        if self.is_manual_player_active and self.is_manual_player_active():
            return
        
        # Şu anda bir etkinlik içinde mi?
        activities = today_schedule.get("activities", [])
        in_any_activity = False
        
        for activity in activities:
            start = activity.get("startTime", "")
            end = activity.get("endTime", "")
            
            if start <= current_time < end:
                in_any_activity = True
                self.in_activity = True
                self.current_activity = activity
                break
        
        # Başlangıçta müzik başlatma - sadece etkinlik bitişinde playMusic kontrolü ile başlar
        if in_any_activity:
            print(f"[Scheduler] Başlangıçta etkinlik içi ({self.current_activity.get('name')}) - müzik başlatılmıyor")
        else:
            # Etkinlik dışındayız. Acaba bir önceki etkinlik müzik çalınmasını istemiş miydi?
            # Ve bir sonraki etkinlikten önce miyiz?
            
            # 1. Şimdi bitmiş olan en son etkinliği bul
            last_ended = None
            for activity in sorted(activities, key=lambda x: x.get("endTime", ""), reverse=True):
                if activity.get("endTime", "") <= current_time:
                    last_ended = activity
                    break
            
            self.last_ended_activity = last_ended
            
            # 2. Eğer son biten etkinlik varsa ve müzik istiyorsa
            if last_ended and last_ended.get("playMusic", False):
                # 3. Sonraki etkinlik (veya gün sonu) gelmediyse çal
                print(f"[Scheduler] Başlangıçta mola ({last_ended.get('name')} sonrası) - müzik kontrolü")
                self._start_background_music()
            else:
                print(f"[Scheduler] Başlangıçta etkinlik dışı - müzik başlatılmıyor")
                self.in_activity = False


# Singleton instance
scheduler = SchedulerService()
