"""
NikolayCo SmartZill v2.0 - Doğum Günü Servisi
Personel doğum günü anonsları yönetimi
"""
import json
from datetime import datetime, date
from typing import List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, SPECIAL_DAYS_FILE


class BirthdayService:
    """Doğum günü yönetim servisi"""
    
    def __init__(self):
        self.data_file = SPECIAL_DAYS_FILE
        self.data = self._load_data()
    
    def _load_data(self) -> dict:
        """Veriyi yükler"""
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "enabled": True,
            "announcement_times": ["09:00", "12:00"],
            "template": "Bugün {name} isimli çalışanımızın doğum günü. Kendisine mutlu yıllar diliyoruz!",
            "people": []
        }
    
    def _save_data(self):
        """Veriyi kaydeder"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_person(self, name: str, birth_date: str) -> bool:
        """Kişi ekler (tarih formatı: DD.MM.YYYY, YYYY-MM-DD veya MM-DD)"""
        try:
            # Tarih formatını normalize et
            if "-" in birth_date and len(birth_date) == 10:  # YYYY-MM-DD
                # DD.MM.YYYY formatına çevir
                parts = birth_date.split("-")
                formatted_date = f"{parts[2]}.{parts[1]}.{parts[0]}"
            elif "-" in birth_date and len(birth_date) == 5:  # MM-DD
                formatted_date = f"01.{birth_date.replace('-', '.')}"
            elif "." in birth_date:  # DD.MM.YYYY veya DD.MM
                formatted_date = birth_date
            else:
                formatted_date = birth_date
            
            person = {
                "name": name,
                "date": formatted_date
            }
            
            # Aynı kişi var mı kontrol et
            for p in self.data["people"]:
                if p["name"].lower() == name.lower():
                    p["date"] = formatted_date
                    self._save_data()
                    return True
            
            self.data["people"].append(person)
            self._save_data()
            return True
            
        except Exception as e:
            print(f"[Birthday] Ekleme hatası: {e}")
            return False
    
    def remove_person(self, name: str) -> bool:
        """Kişi siler"""
        original_count = len(self.data["people"])
        self.data["people"] = [
            p for p in self.data["people"]
            if p["name"].lower() != name.lower()
        ]
        
        if len(self.data["people"]) < original_count:
            self._save_data()
            return True
        return False
    
    def get_todays_birthdays(self) -> List[dict]:
        """Bugünkü doğum günlerini döndürür"""
        today = date.today()
        today_str = today.strftime("%d.%m")  # DD.MM formatı
        
        result = []
        for p in self.data["people"]:
            person_date = p.get("date", "")
            # DD.MM.YYYY veya DD.MM formatından DD.MM çıkar
            if person_date:
                parts = person_date.split(".")
                if len(parts) >= 2:
                    person_day_month = f"{parts[0]}.{parts[1]}"
                    if person_day_month == today_str:
                        result.append(p)
        
        return result
    
    def get_upcoming_birthdays(self, days: int = 30) -> List[dict]:
        """Yaklaşan doğum günlerini listeler"""
        today = date.today()
        upcoming = []
        
        for person in self.data["people"]:
            try:
                month, day = map(int, person["date"].split("-"))
                
                # Bu yıl için tarih
                try:
                    birthday = date(today.year, month, day)
                except ValueError:
                    continue
                
                # Geçmişse gelecek yıl al
                if birthday < today:
                    birthday = date(today.year + 1, month, day)
                
                days_until = (birthday - today).days
                if days_until <= days:
                    upcoming.append({
                        "name": person["name"],
                        "date": person["date"],
                        "days_until": days_until
                    })
            except:
                continue
        
        return sorted(upcoming, key=lambda x: x["days_until"])
    
    def import_from_csv(self, content: str) -> int:
        """CSV'den içe aktarır (format: isim,tarih)"""
        imported = 0
        lines = content.strip().split("\n")
        
        for line in lines:
            if not line.strip() or line.startswith("#"):
                continue
            
            parts = line.split(",")
            if len(parts) >= 2:
                name = parts[0].strip()
                date_str = parts[1].strip()
                if self.add_person(name, date_str):
                    imported += 1
        
        return imported
    
    def import_from_excel(self, file_path: str) -> int:
        """Excel'den içe aktarır"""
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            
            # Kolon isimlerini kontrol et
            name_cols = ["name", "Name", "İsim", "isim", "Ad", "ad", "Adı", "adı", "Ad Soyad", "Ad-Soyad"]
            date_cols = ["date", "Date", "Tarih", "tarih", "Doğum Tarihi", "doğum tarihi", "Doğum", "doğum", "Birthday", "birth_date"]
            
            name_col = None
            date_col = None
            
            for col in df.columns:
                if name_col is None and col in name_cols:
                    name_col = col
                if date_col is None and col in date_cols:
                    date_col = col
            
            # İlk iki kolon al eğer bulunamazsa
            if name_col is None and len(df.columns) >= 1:
                name_col = df.columns[0]
            if date_col is None and len(df.columns) >= 2:
                date_col = df.columns[1]
            
            if name_col is None or date_col is None:
                print("[Birthday] Excel kolonları bulunamadı")
                return 0
            
            imported = 0
            for _, row in df.iterrows():
                name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
                date_val = row[date_col]
                
                if not name or name == "nan":
                    continue
                
                # Tarih formatını belirle
                if pd.isna(date_val):
                    continue
                elif isinstance(date_val, datetime):
                    date_str = date_val.strftime("%d.%m.%Y")
                elif hasattr(date_val, 'strftime'):
                    date_str = date_val.strftime("%d.%m.%Y")
                else:
                    date_str = str(date_val).strip()
                
                if date_str and date_str != "nan":
                    if self.add_person(name, date_str):
                        imported += 1
            
            return imported
            
        except Exception as e:
            print(f"[Birthday] Excel import hatası: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def set_enabled(self, enabled: bool):
        """Doğum günü anonslarını açar/kapatır"""
        self.data["enabled"] = enabled
        self._save_data()
    
    def set_announcement_times(self, times: List[str]):
        """Anons saatlerini ayarlar"""
        self.data["announcement_times"] = times
        self._save_data()
    
    def set_template(self, template: str):
        """Anons şablonunu ayarlar"""
        self.data["template"] = template
        self._save_data()
    
    def get_announcement_text(self, name: str) -> str:
        """Anons metnini oluşturur"""
        return self.data["template"].format(name=name)
    
    def should_announce_now(self) -> List[str]:
        """Şu an anons zamanı ise kişi adlarını döndürür"""
        if not self.data.get("enabled", True):
            return []
        
        current_time = datetime.now().strftime("%H:%M")
        
        if current_time not in self.data.get("announcement_times", []):
            return []
        
        birthdays = self.get_todays_birthdays()
        return [b["name"] for b in birthdays]
    
    
    def get_all_people(self) -> List[dict]:
        """Tüm kişileri döndürür"""
        return self.data["people"]
    
    def get_status(self) -> dict:
        """Servis durumunu döndürür"""
        return {
            "enabled": self.data.get("enabled", True),
            "announcement_times": self.data.get("announcement_times", ["09:00", "12:00"]),
            "template": self.data.get("template", ""),
            "total_people": len(self.data["people"]),
            "people": self.data["people"],
            "todays_birthdays": self.get_todays_birthdays(),
            "upcoming_birthdays": self.get_upcoming_birthdays(7)
        }


# Singleton instance
birthday_service = BirthdayService()
