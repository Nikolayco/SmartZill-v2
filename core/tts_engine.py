"""
NikolayCo SmartZill v2.0 - TTS Motoru
Edge TTS tabanlı metin-ses dönüştürücü
"""
import asyncio
import os
import uuid
from pathlib import Path
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANNOUNCEMENTS_DIR

# TTS sesleri
VOICES = {
    "tr": {
        "male": "tr-TR-AhmetNeural",
        "female": "tr-TR-EmelNeural"
    },
    "en": {
        "male": "en-US-GuyNeural",
        "female": "en-US-JennyNeural"
    },
    "de": {
        "male": "de-DE-ConradNeural",
        "female": "de-DE-KatjaNeural"
    },
    "ru": {
        "male": "ru-RU-DmitryNeural",
        "female": "ru-RU-SvetlanaNeural"
    },
    "bg": {
        "male": "bg-BG-BorislavNeural",
        "female": "bg-BG-KalinaNeural"
    }
}


class TTSEngine:
    """Edge TTS tabanlı metin-ses motoru"""
    
    def __init__(self):
        self.language = "tr"
        self.gender = "female"  # Emel sesi varsayılan
        self.rate = "+0%"
        self.tts_dir = ANNOUNCEMENTS_DIR / "tts"
        self.tts_dir.mkdir(parents=True, exist_ok=True)
    
    def get_voice(self) -> str:
        """Aktif sesi döndürür"""
        lang_voices = VOICES.get(self.language, VOICES["tr"])
        return lang_voices.get(self.gender, lang_voices["male"])
    
    def set_language(self, language: str):
        """Dili ayarlar"""
        if language in VOICES:
            self.language = language
    
    def set_gender(self, gender: str):
        """Cinsiyeti ayarlar (male/female)"""
        if gender in ("male", "female"):
            self.gender = gender
    
    def set_rate(self, rate: str):
        """Konuşma hızını ayarlar (örn: +10%, -20%)"""
        self.rate = rate
    
    async def _generate_core(self, text: str, output_path: str) -> bool:
        """Core async generation logic"""
        try:
            import edge_tts
            
            voice = self.get_voice()
            communicate = edge_tts.Communicate(text, voice, rate=self.rate)
            await communicate.save(output_path)
            return True
            
        except Exception as e:
            print(f"[TTS] Hata: {e}")
            return False

    async def generate_async(self, text: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Async olarak ses dosyası oluşturur (FastAPI için)
        """
        if not text.strip():
            return None
        
        if filename is None:
            filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
        
        output_path = str(self.tts_dir / filename)
        
        if await self._generate_core(text, output_path):
            return output_path
        return None

    def generate(self, text: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Senkron wrapper - Thread güvenli
        """
        if not text.strip():
            return None
        
        if filename is None:
            filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
        
        output_path = str(self.tts_dir / filename)
        
        # Async fonksiyonu çalıştır
        try:
            # Mevcut event loop'u kontrol et
            try:
                loop = asyncio.get_running_loop()
                # Loop varsa, thread içinde yeni loop açarak çalıştır
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._sync_generate, text, output_path)
                    success = future.result(timeout=30)
            except RuntimeError:
                # Loop yoksa (örn: CLI script) direkt çalıştır
                success = self._sync_generate(text, output_path)
                
        except Exception as e:
            print(f"[TTS] Wrapper hatası: {e}")
            return None
        
        if success and os.path.exists(output_path):
            return output_path
        return None
    
    def _sync_generate(self, text: str, output_path: str) -> bool:
        """Sync context'te TTS oluştur (Yeni loop ile)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(self._generate_core(text, output_path))
            loop.close()
            return success
        except Exception as e:
            print(f"[TTS] Sync generate hatası: {e}")
            return False
    
    def generate_birthday(self, name: str, template: Optional[str] = None) -> Optional[str]:
        """Doğum günü anonsu oluşturur"""
        # Şablon verilmemişse varsayılan kullan
        if template is None:
            template = "Bugün {name} isimli çalışanımızın doğum günü. Kendisine mutlu yıllar diliyoruz!"
        
        # Şablondaki {name} yerine gerçek ismi koy
        text = template.format(name=name)
        return self.generate(text, f"birthday_{name.replace(' ', '_')}.mp3")
    
    def cleanup_old_files(self, max_age_days: int = 7):
        """Eski TTS dosyalarını temizler"""
        import time
        
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        for f in self.tts_dir.iterdir():
            if f.suffix == ".mp3":
                age = now - f.stat().st_mtime
                if age > max_age_seconds:
                    try:
                        f.unlink()
                    except:
                        pass
    
    def get_available_voices(self) -> dict:
        """Mevcut sesleri döndürür"""
        return VOICES


# Singleton instance
tts_engine = TTSEngine()
