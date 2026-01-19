"""
NikolayCo SmartZill v2.0 - Tatil Servisi
Resmi tatil günleri yönetimi
"""
import holidays
from datetime import datetime, date
from typing import List, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import load_config, save_config


class HolidayService:
    """Resmi tatil günleri servisi"""
    
    # Tüm desteklenen ülkeler
    SUPPORTED_COUNTRIES = {
        "TR": "Türkiye", "US": "ABD", "GB": "İngiltere", "DE": "Almanya",
        "FR": "Fransa", "IT": "İtalya", "ES": "İspanya", "PT": "Portekiz",
        "NL": "Hollanda", "BE": "Belçika", "AT": "Avusturya", "CH": "İsviçre",
        "PL": "Polonya", "CZ": "Çekya", "HU": "Macaristan", "RO": "Romanya",
        "BG": "Bulgaristan", "GR": "Yunanistan", "RU": "Rusya", "UA": "Ukrayna",
        "SE": "İsveç", "NO": "Norveç", "DK": "Danimarka", "FI": "Finlandiya",
        "IE": "İrlanda", "AU": "Avustralya", "NZ": "Yeni Zelanda", "CA": "Kanada",
        "MX": "Meksika", "BR": "Brezilya", "AR": "Arjantin", "JP": "Japonya",
        "KR": "Güney Kore", "CN": "Çin", "IN": "Hindistan", "SA": "S. Arabistan",
        "AE": "BAE", "EG": "Mısır", "ZA": "G. Afrika", "IL": "İsrail"
    }
    
    def __init__(self):
        self.config = load_config()
        self.country = self.config.get("holidays", {}).get("country", "TR")
        self.enabled = self.config.get("holidays", {}).get("enabled", True)
        self.skip_on_holidays = self.config.get("holidays", {}).get("skip_on_holidays", True)
        self._holidays_cache = None
        self._cache_year = None
    
    def _get_holidays(self, year: int = None) -> holidays.HolidayBase:
        """Tatil verilerini alır (cache'li)"""
        if year is None:
            year = datetime.now().year
        
        if self._holidays_cache is None or self._cache_year != year:
            try:
                self._holidays_cache = holidays.country_holidays(self.country, years=year)
                self._cache_year = year
            except Exception as e:
                print(f"[Holidays] Hata: {e}")
                self._holidays_cache = {}
        
        return self._holidays_cache
    
    def is_holiday_today(self) -> bool:
        """Bugün tatil mi kontrol eder (ve sessize alınmamış mı)"""
        if not self.enabled or not self.skip_on_holidays:
            return False
        
        today = date.today()
        holidays_data = self._get_holidays(today.year)
        
        # Tatil değilse False
        if today not in holidays_data:
            return False
        
        # Tatil ama sessize alınmışsa False (normal çalışma)
        date_str = today.strftime("%d.%m.%Y")
        muted_holidays = self._get_muted_holidays()
        
        return date_str not in muted_holidays
    
    def _get_muted_holidays(self) -> set:
        """Sessize alınmış tatilleri döndürür"""
        config = load_config()
        return set(config.get("holidays", {}).get("muted_dates", []))
    
    def set_holiday_muted(self, date_str: str, muted: bool):
        """Belirli bir tatili sessize al veya aktif et"""
        config = load_config()
        if "holidays" not in config:
            config["holidays"] = {}
        if "muted_dates" not in config["holidays"]:
            config["holidays"]["muted_dates"] = []
        
        muted_list = config["holidays"]["muted_dates"]
        
        if muted and date_str not in muted_list:
            muted_list.append(date_str)
        elif not muted and date_str in muted_list:
            muted_list.remove(date_str)
        
        save_config(config)
    
    def get_holiday_name(self, check_date: date = None) -> Optional[str]:
        """Verilen tarihin tatil adını döndürür"""
        if check_date is None:
            check_date = date.today()
        
        holidays_data = self._get_holidays(check_date.year)
        return holidays_data.get(check_date)
    
    def get_all_holidays(self, year: int = None) -> List[dict]:
        """Yılın tüm tatillerini listeler"""
        if year is None:
            year = datetime.now().year
        
        try:
            holidays_data = holidays.country_holidays(self.country, years=year)
        except Exception:
            return []
        
        # Sessize alınmış tatilleri al
        muted_holidays = self._get_muted_holidays()
        
        all_holidays = []
        for holiday_date, name in sorted(holidays_data.items()):
            date_str = holiday_date.strftime("%d.%m.%Y")
            all_holidays.append({
                "date": date_str,
                "name": name,
                "muted": date_str in muted_holidays
            })
        
        return all_holidays
    
    def get_upcoming_holidays(self, count: int = 5) -> List[dict]:
        """Yaklaşan tatilleri listeler"""
        today = date.today()
        holidays_data = self._get_holidays(today.year)
        
        # Gelecek yılı da ekle
        try:
            next_year = holidays.country_holidays(self.country, years=today.year + 1)
            holidays_data.update(next_year)
        except Exception:
            pass
        
        upcoming = []
        for holiday_date, name in sorted(holidays_data.items()):
            if holiday_date >= today:
                upcoming.append({
                    "date": holiday_date.strftime("%d.%m.%Y"),
                    "name": name,
                    "days_until": (holiday_date - today).days
                })
                if len(upcoming) >= count:
                    break
        
        return upcoming
    
    def set_country(self, country: str):
        """Ülkeyi değiştirir"""
        self.country = country
        self._holidays_cache = None
        
        # Config'e kaydet
        config = load_config()
        if "holidays" not in config:
            config["holidays"] = {}
        config["holidays"]["country"] = country
        save_config(config)
    
    def set_enabled(self, enabled: bool):
        """Tatil kontrolünü açar/kapatır"""
        self.enabled = enabled
        config = load_config()
        if "holidays" not in config:
            config["holidays"] = {}
        config["holidays"]["enabled"] = enabled
        save_config(config)
    
    def set_skip_on_holidays(self, skip: bool):
        """Tatillerde sessizliği açar/kapatır"""
        self.skip_on_holidays = skip
        config = load_config()
        if "holidays" not in config:
            config["holidays"] = {}
        config["holidays"]["skip_on_holidays"] = skip
        save_config(config)
    
    def get_status(self) -> dict:
        """Tatil durumunu döndürür"""
        today_holiday = self.get_holiday_name()
        return {
            "enabled": self.enabled,
            "skip_on_holidays": self.skip_on_holidays,
            "country": self.country,
            "country_name": self.SUPPORTED_COUNTRIES.get(self.country, self.country),
            "is_holiday_today": self.is_holiday_today(),
            "today_holiday_name": today_holiday,
            "upcoming_holidays": self.get_upcoming_holidays(10),
            "all_holidays": self.get_all_holidays()
        }


# Singleton instance
holiday_service = HolidayService()
