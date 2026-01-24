import os
import sys
import platform
from pathlib import Path

# Proje kök dizinini ve VLC yolunu ayarla
ROOT = Path(__file__).parent.parent.resolve()
if platform.system() == "Windows":
    # Öncelik: Çevre değişkeni -> Proje içi bin/vlc -> Standart yollar
    vlc_local_path = os.environ.get("SMARTZILL_VLC_PATH")
    if not vlc_local_path:
        local_vlc_dir = ROOT / "bin" / "vlc"
        if local_vlc_dir.exists():
            vlc_local_path = str(local_vlc_dir)
            
    if vlc_local_path and os.path.exists(vlc_local_path):
        dll_path = os.path.join(vlc_local_path, "libvlc.dll")
        if os.path.exists(dll_path):
            print(f"[*] VLC yukleniyor: {vlc_local_path}")
            # python-vlc için yolu ayarla
            os.environ["PYTHON_VLC_LIB_PATH"] = dll_path
            
            # Python 3.8+ için DLL dizini ekle (bağımlılıklar için)
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(vlc_local_path)
            else:
                os.environ['PATH'] = vlc_local_path + os.pathsep + os.environ['PATH']
        else:
            print(f"[!] UYARI: Portatif klasor bulundu ama libvlc.dll yok: {vlc_local_path}")
    else:
        print("[*] Sistem VLC kullaniliyor (Standart yollar)")

import vlc
import time
import threading
import os
from pathlib import Path
from typing import Optional, Callable
import sys

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import load_config, save_config, BELLS_DIR, ANNOUNCEMENTS_DIR, MUSIC_DIR


class AudioChannel:
    """Tek bir ses kanalı"""
    
    def __init__(self, name: str, volume: int = 100):
        self.name = name
        self.volume = max(0, min(100, volume))
        self.player: Optional[vlc.MediaPlayer] = None
        self.instance = vlc.Instance("--no-xlib", "--quiet")
        self.is_paused = False
        self.current_source: Optional[str] = None
        
    def play(self, source: str, is_stream: bool = False) -> bool:
        """Ses kaynağını oynatır"""
        try:
            self.stop()
            
            if is_stream:
                media = self.instance.media_new(source)
            else:
                if not os.path.exists(source):
                    print(f"[{self.name}] Dosya bulunamadı: {source}")
                    return False
                media = self.instance.media_new_path(source)
            
            self.player = self.instance.media_player_new()
            self.player.set_media(media)
            self.player.audio_set_volume(self.volume)
            self.player.play()
            self.current_source = source
            self.is_paused = False
            
            # Oynatma başlamasını bekle
            time.sleep(0.1)
            return True
            
        except Exception as e:
            print(f"[{self.name}] Oynatma hatası: {e}")
            return False
    
    def stop(self):
        """Oynatmayı durdurur"""
        if self.player:
            try:
                self.player.stop()
                self.player.release()
            except:
                pass
            self.player = None
        self.is_paused = False
        self.current_source = None
    
    def pause(self):
        """Oynatmayı duraklatır"""
        if self.player and self.is_playing():
            self.player.pause()
            self.is_paused = True
    
    def resume(self):
        """Oynatmayı devam ettirir"""
        if self.player and self.is_paused:
            self.player.play()
            self.is_paused = False
    
    def set_volume(self, volume: int):
        """Ses seviyesini ayarlar (0-100)"""
        self.volume = max(0, min(100, volume))
        if self.player:
            self.player.audio_set_volume(self.volume)
    
    def is_playing(self) -> bool:
        """Oynatma durumunu kontrol eder"""
        if not self.player:
            return False
        state = self.player.get_state()
        return state in (vlc.State.Playing, vlc.State.Opening, vlc.State.Buffering)
    
    def get_position(self) -> float:
        """Oynatma pozisyonunu döndürür (0.0-1.0)"""
        if self.player:
            return self.player.get_position() or 0.0
        return 0.0
    
    def get_duration(self) -> int:
        """Toplam süreyi milisaniye olarak döndürür"""
        if self.player:
            return self.player.get_length() or 0
        return 0


class AudioEngine:
    """
    Çok kanallı ses motoru
    
    Kanallar ve öncelik sırası:
    1. bell (zil) - En yüksek öncelik, her şeyi keser
    2. announcement (anons) - Müziği keser
    3. music (mola müziği) - Otomatik mola müziği
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        
        # Yapılandırmayı yükle
        config = load_config()
        volumes = config.get("volumes", {})
        
        # Kanalları oluştur
        self.channels = {
            "bell": AudioChannel("bell", volumes.get("bell", 100)),
            "announcement": AudioChannel("announcement", volumes.get("announcement", 80)),
            "music": AudioChannel("music", volumes.get("music", 60)),
        }
        
        # Müzik duraklatma durumu
        self._music_was_playing = False
        
        # Callback fonksiyonlar
        self.on_bell_start: Optional[Callable] = None
        self.on_bell_end: Optional[Callable] = None
        
    def _resolve_path(self, filename: str, default_dir: Path) -> str:
        """Dosya yolunu çözümler"""
        if os.path.isabs(filename):
            return filename
        
        # Önce verilen dizinde ara
        path = default_dir / filename
        if path.exists():
            return str(path)
        
        # Eğer filename 'default.mp3' ise ve bulunamadıysa, sessizce geç
        if filename == 'default.mp3':
            return None
        
        # Tüm ses dizinlerinde ara
        for dir_path in [BELLS_DIR, ANNOUNCEMENTS_DIR, MUSIC_DIR]:
            path = dir_path / filename
            if path.exists():
                return str(path)
        
        return filename
    
    def play_bell(self, filename: str, blocking: bool = True) -> bool:
        """
        Zil çalar - en yüksek öncelik
        Diğer tüm kanalları duraklatır
        """
        with self.lock:
            # Müzik çalıyorsa duraklat
            if self.channels["music"].is_playing():
                self._music_was_playing = True
                self.channels["music"].pause()
            
            # Anonsu durdur
            self.channels["announcement"].stop()
            
            # Zili çal
            path = self._resolve_path(filename, BELLS_DIR)
            success = self.channels["bell"].play(path)
            
            if self.on_bell_start:
                self.on_bell_start()
        
        if blocking and success:
            # Zil bitene kadar bekle
            while self.channels["bell"].is_playing():
                time.sleep(0.1)
            
            with self.lock:
                # Müziği devam ettir
                if self._music_was_playing:
                    self.channels["music"].resume()
                    self._music_was_playing = False
                
                if self.on_bell_end:
                    self.on_bell_end()
        
        return success
    
    def play_announcement(self, filename: str, blocking: bool = True) -> bool:
        """
        Anons çalar
        Müziği duraklatır, zil çalarken bekler
        """
        # Zil çalıyorsa bekle
        while self.channels["bell"].is_playing():
            time.sleep(0.1)
        
        with self.lock:
            # Müzik çalıyorsa duraklat
            if self.channels["music"].is_playing():
                self._music_was_playing = True
                self.channels["music"].pause()
            
            # Anonsu çal
            path = self._resolve_path(filename, ANNOUNCEMENTS_DIR)
            success = self.channels["announcement"].play(path)
        
        if blocking and success:
            while self.channels["announcement"].is_playing():
                time.sleep(0.1)
            
            with self.lock:
                if self._music_was_playing:
                    self.channels["music"].resume()
                    self._music_was_playing = False
        
        return success
    
    def play_music(self, source: str, is_stream: bool = False) -> bool:
        """
        Mola müziği çalar
        Zil veya anons çalıyorsa başlatmaz
        """
        if self.channels["bell"].is_playing() or self.channels["announcement"].is_playing():
            return False
        
        with self.lock:
            if is_stream:
                return self.channels["music"].play(source, is_stream=True)
            else:
                path = self._resolve_path(source, MUSIC_DIR)
                return self.channels["music"].play(path)
    
    def stop_music(self):
        """Mola müziğini durdurur"""
        with self.lock:
            self.channels["music"].stop()
            self._music_was_playing = False
    
    def stop_all(self):
        """Tüm kanalları durdurur"""
        with self.lock:
            for channel in self.channels.values():
                channel.stop()
            self._music_was_playing = False
    
    def set_volume(self, channel: str, volume: int):
        """Kanal ses seviyesini ayarlar"""
        if channel in self.channels:
            self.channels[channel].set_volume(volume)
            
            # Yapılandırmaya kaydet
            config = load_config()
            config["volumes"][channel] = volume
            save_config(config)
    
    def get_volume(self, channel: str) -> int:
        """Kanal ses seviyesini döndürür"""
        if channel in self.channels:
            return self.channels[channel].volume
        return 0
    
    def get_status(self) -> dict:
        """Tüm kanalların durumunu döndürür"""
        status = {}
        for name, channel in self.channels.items():
            status[name] = {
                "playing": channel.is_playing(),
                "paused": channel.is_paused,
                "volume": channel.volume,
                "source": channel.current_source,
                "position": channel.get_position(),
                "duration": channel.get_duration()
            }
        return status
    
    def play_sequence(self, files: list, channel: str = "bell") -> bool:
        """Dosya listesini sırayla çalar"""
        for filename in files:
            if channel == "bell":
                self.play_bell(filename, blocking=True)
            elif channel == "announcement":
                self.play_announcement(filename, blocking=True)
            else:
                return False
        return True


# Singleton instance
audio_engine = AudioEngine()
