"""
NikolayCo SmartZill v2.0 - Yedekleme Servisi
JSON ve Excel yedekleme/geri yükleme
"""
import json
import shutil
import copy
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    DATA_DIR, SOUNDS_DIR, CONFIG_FILE, SCHEDULE_FILE, SPECIAL_DAYS_FILE,
    load_config, save_config, load_schedule, save_schedule
)


class BackupService:
    """Yedekleme ve geri yükleme servisi"""
    
    def __init__(self):
        self.backup_dir = DATA_DIR / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = 10
    
    def _get_sanitized_config(self) -> dict:
        """Config'in şifreden arındırılmış kopyasını döndürür"""
        config = copy.deepcopy(load_config())
        # Güvenlik ve şifre bilgilerini temizle
        if "security" in config:
            if "admin_password" in config["security"]:
                config["security"]["admin_password"] = "" # Boş bırak
        return config

    def create_backup_json(self) -> str:
        """JSON formatında yedek oluşturur"""
        backup_data = {
            "version": "2.0",
            "created_at": datetime.now().isoformat(),
            "config": self._get_sanitized_config(),
            "schedule": load_schedule(),
            "special_days": self._load_special_days()
        }
        
        filename = f"NikolayCo_SmartZill_Yedek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.backup_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        self._cleanup_old_backups()
        return str(filepath)
    
    def create_backup_excel(self) -> str:
        """Excel formatında yedek oluşturur"""
        try:
            import pandas as pd
            from io import BytesIO
            
            filename = f"NikolayCo_SmartZill_Yedek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = self.backup_dir / filename
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Haftalık Program
                schedule = load_schedule()
                schedule_rows = []
                
                for day in schedule:
                    for activity in day.get("activities", []):
                        schedule_rows.append({
                            "Gün": day.get("dayName", ""),
                            "Gün No": day.get("dayOfWeek", 0),
                            "Aktif": day.get("enabled", True),
                            "Etkinlik Adı": activity.get("name", ""),
                            "Başlangıç": activity.get("startTime", ""),
                            "Bitiş": activity.get("endTime", ""),
                            "Başlangıç Zili": activity.get("startSoundId", ""),
                            "Bitiş Zili": activity.get("endSoundId", ""),
                            "Müzik": activity.get("playMusic", False)
                        })
                
                if schedule_rows:
                    pd.DataFrame(schedule_rows).to_excel(writer, sheet_name="Haftalık Program", index=False)
                
                # Doğum Günleri
                special_days = self._load_special_days()
                if special_days.get("people"):
                    pd.DataFrame(special_days["people"]).to_excel(
                        writer, sheet_name="Doğum Günleri", index=False
                    )
                
                # Ses Dosyaları
                sound_files = self._list_sound_files()
                if sound_files:
                    pd.DataFrame(sound_files).to_excel(writer, sheet_name="Ses Dosyaları", index=False)
                
                # Sistem Ayarları
                config = self._get_sanitized_config()
                config_rows = []
                for key, value in config.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            config_rows.append({
                                "Kategori": key,
                                "Ayar": sub_key,
                                "Değer": str(sub_value)
                            })
                    else:
                        config_rows.append({
                            "Kategori": "",
                            "Ayar": key,
                            "Değer": str(value)
                        })
                
                pd.DataFrame(config_rows).to_excel(writer, sheet_name="Ayarlar", index=False)
            
            self._cleanup_old_backups()
            return str(filepath)
            
        except Exception as e:
            print(f"[Backup] Excel oluşturma hatası: {e}")
            # JSON'a geri dön
            return self.create_backup_json()
    
    def restore_from_json(self, filepath: str) -> bool:
        """JSON yedeğinden geri yükler"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
            
            # Versiyon kontrolü
            version = backup_data.get("version", "1.0")
            
            # Config
            if "config" in backup_data:
                new_config = backup_data["config"]
                
                # GÜVENLİK: Mevcut şifreyi ASLA değiştirme
                # Yedeği yüklerken, sistemin o anki şifresini al ve yeni konfigürasyona zorla
                current_config = load_config()
                if "security" in current_config and "admin_password" in current_config["security"]:
                    # Eğer new_config içinde security kısmı yoksa oluştur
                    if "security" not in new_config:
                        new_config["security"] = {}
                    
                    # Mevcut şifreyi geri yükle
                    new_config["security"]["admin_password"] = current_config["security"]["admin_password"]
                
                save_config(new_config)
            
            # Schedule
            if "schedule" in backup_data:
                save_schedule(backup_data["schedule"])
            
            # Special days
            if "special_days" in backup_data:
                self._save_special_days(backup_data["special_days"])
            
            return True
            
        except Exception as e:
            print(f"[Backup] Geri yükleme hatası: {e}")
            return False
    
    def restore_from_excel(self, filepath: str) -> bool:
        """Excel yedeğinden geri yükler"""
        try:
            import pandas as pd
            
            xl = pd.ExcelFile(filepath)
            
            # Haftalık Program
            if "Haftalık Program" in xl.sheet_names:
                df = pd.read_excel(xl, "Haftalık Program")
                schedule = load_schedule()
                
                # Mevcut etkinlikleri temizle
                for day in schedule:
                    day["activities"] = []
                
                # Yeni etkinlikleri ekle
                for _, row in df.iterrows():
                    day_idx = int(row.get("Gün No", 0))
                    for day in schedule:
                        if day.get("dayOfWeek") == day_idx:
                            day["enabled"] = bool(row.get("Aktif", True))
                            day["activities"].append({
                                "id": f"activity_{datetime.now().timestamp()}_{len(day['activities'])}",
                                "name": str(row.get("Etkinlik Adı", "")),
                                "startTime": str(row.get("Başlangıç", "")),
                                "endTime": str(row.get("Bitiş", "")),
                                "startSoundId": str(row.get("Başlangıç Zili", "")),
                                "endSoundId": str(row.get("Bitiş Zili", "")),
                                "playMusic": bool(row.get("Müzik", False))
                            })
                            break
                
                save_schedule(schedule)
            
            # Doğum Günleri
            if "Doğum Günleri" in xl.sheet_names:
                df = pd.read_excel(xl, "Doğum Günleri")
                special_days = self._load_special_days()
                special_days["people"] = df.to_dict("records")
                self._save_special_days(special_days)
            
            return True
            
        except Exception as e:
            print(f"[Backup] Excel geri yükleme hatası: {e}")
            return False
    
    def get_backup_list(self) -> List[dict]:
        """Mevcut yedekleri listeler"""
        backups = []
        
        for f in sorted(self.backup_dir.iterdir(), reverse=True):
            if f.suffix in (".json", ".xlsx"):
                backups.append({
                    "filename": f.name,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    "type": "json" if f.suffix == ".json" else "excel"
                })
        
        return backups[:self.max_backups]
    
    def delete_backup(self, filename: str) -> bool:
        """Yedeği siler"""
        filepath = self.backup_dir / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False
    
    def _cleanup_old_backups(self):
        """Eski yedekleri temizler"""
        backups = sorted(
            [f for f in self.backup_dir.iterdir() if f.suffix in (".json", ".xlsx")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for old_backup in backups[self.max_backups:]:
            try:
                old_backup.unlink()
            except:
                pass
    
    def _load_special_days(self) -> dict:
        """Özel günleri yükler"""
        if SPECIAL_DAYS_FILE.exists():
            try:
                with open(SPECIAL_DAYS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"enabled": True, "people": []}
    
    def _save_special_days(self, data: dict):
        """Özel günleri kaydeder"""
        with open(SPECIAL_DAYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _list_sound_files(self) -> List[dict]:
        """Ses dosyalarını listeler"""
        files = []
        
        for subdir in ["bells", "announcements", "music", "system"]:
            dir_path = SOUNDS_DIR / subdir
            if dir_path.exists():
                for f in dir_path.iterdir():
                    if f.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac", ".m4a"):
                        files.append({
                            "Klasör": subdir,
                            "Dosya": f.name,
                            "Boyut": f.stat().st_size
                        })
        
        return files
    
    def export_to_bytes(self, format: str = "json") -> bytes:
        """Yedeği byte olarak döndürür (indirme için)"""
        if format == "excel":
            filepath = self.create_backup_excel()
        else:
            filepath = self.create_backup_json()
        
        with open(filepath, "rb") as f:
            return f.read()


# Singleton instance
backup_service = BackupService()
