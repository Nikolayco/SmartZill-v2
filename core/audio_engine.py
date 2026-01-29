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
import platform
from pathlib import Path
from typing import Optional, Callable
import sys

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import load_config, save_config, BELLS_DIR, ANNOUNCEMENTS_DIR, MUSIC_DIR
import random


class AudioChannel:
    """Tek bir ses kanalı"""
    
    def __init__(self, name: str, volume: int = 100):
        self.name = name
        # Windows'ta müzik kanalı varsayılan olarak daha yüksek sesle başlasın (80)
        if platform.system() == "Windows" and name == "music" and volume == 60:
            volume = 80
        self.volume = max(0, min(100, volume))
        self.player: Optional[vlc.MediaPlayer] = None
        # Windows'ta extra ses seçenekleri
        if platform.system() == "Windows":
            self.instance = vlc.Instance("--quiet", "--alsa-mixer-index=-1")
        else:
            self.instance = vlc.Instance("--no-xlib", "--quiet")
        self.is_paused = False
        self.current_source: Optional[str] = None
        
        # Playlist desteği
        self.playlist: list = []
        self.playlist_index: int = 0
        self.shuffle: bool = False
        self.is_playlist_mode: bool = False
        
        # Thread safety
        self.lock = threading.RLock()


        
    def play(self, source: str, is_stream: bool = False, is_playlist_track: bool = False) -> bool:
        """Ses kaynağını oynatır"""
        with self.lock:
            try:
                # Playlist modu değilse ve yeni bir tekli dosya çağrıldıysa playlist'i temizle
                if not is_playlist_track:
                    self.playlist = []
                    self.is_playlist_mode = False
                
                self.stop(stop_playlist=not is_playlist_track)

                # Eğer kaynak geçersizse (None veya boş) sessizce başarısız ol
                if not source:
                    print(f"[{self.name}] Geçersiz ses kaynağı: {source!r}")
                    return False

                if is_stream:
                    media = self.instance.media_new(source)
                else:
                    if not os.path.exists(source):
                        print(f"[{self.name}] Dosya bulunamadı: {source}")
                        return False
                    media = self.instance.media_new_path(source)
                
                self.player = self.instance.media_player_new()
                self.player.set_media(media)
                
                # Windows'ta ses seviyesi ayarlaması
                if platform.system() == "Windows":
                    adjusted_volume = min(255, int((self.volume / 100) * 255))
                    adjusted_volume = max(100, adjusted_volume)
                    self.player.audio_set_volume(adjusted_volume)
                else:
                    self.player.audio_set_volume(self.volume)
                
                # Parça bitiş olayını dinle
                event_manager = self.player.event_manager()
                event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_track_end)

                # Not: MediaPlayerEncounteredError event'ine bağlanmak test harness'ını
                # etkileyebildiği için bu projede doğrudan event'e bağlanmıyoruz.
                # Hata tespiti için AudioEngine seviyesinde kontrol/monitor thread'i kullanılacak.

                self.player.play()
                self.current_source = source
                self.is_paused = False
                
                # Oynatma başlamasını bekle
                time.sleep(0.1)
                return True
                
            except Exception as e:
                print(f"[{self.name}] Oynatma hatası: {e}")
                return False
            
            
    def play_playlist(self, files: list, shuffle: bool = False) -> bool:
        """Playlist oynatır"""
        with self.lock:
            if not files:
                return False
                
            self.playlist = files.copy()
            self.shuffle = shuffle
            self.playlist_index = 0
            self.is_playlist_mode = True
            
            if self.shuffle:
                random.shuffle(self.playlist)
                
            # İlk parçayı oynat
            return self.play(self.playlist[0], is_playlist_track=True)

    def _on_track_end(self, event):
        """Parça bittiğinde"""
        if self.is_playlist_mode and self.playlist:
            # Thread içinde bir sonraki parçayı tetikle
            threading.Thread(target=self._play_next, daemon=True).start()

            
    def _play_next(self):
        """Sıradaki parçayı oynat"""
        with self.lock:
            if not self.is_playlist_mode:
                return
                
            self.playlist_index += 1
            
            # Playlist bitti mi?
            if self.playlist_index >= len(self.playlist):
                if self.shuffle:
                    # Tekrar karıştır ve başa dön (Sürekli döngü)
                    random.shuffle(self.playlist)
                    self.playlist_index = 0
                else:
                    # Düz listede başa dön
                    self.playlist_index = 0
            
            if self.playlist:
                next_file = self.playlist[self.playlist_index]
                self.play(next_file, is_playlist_track=True)
    
    def stop(self, stop_playlist: bool = True):
        """Oynatmayı durdurur"""
        # stop metodunda lock kullanmıyoruz çünkü play metodunun içinde çağrılıyor
        # ve play metodu zaten kilitli. RLock recursive olsa da karışıklığı önlemek için
        # çağrılan yer lock almalı. Ancak dışarıdan çağrılma ihtimaline karşı:
        
        # Eğer caller lock almamışsa biz alalım (basit kontrol zor, o yüzden RLock güvenli)
        
        # NOT: RLock aynı thread için kilitlemeye izin verir.
        # play -> stop zincirinde sorun olmaz.
        # Ancak dışarıdan doğrudan stop çağrıldığında kilit lazım.
        
        # Bu yüzden tüm bloklarda with self.lock kullanmak en güvenlisi (RLock sayesinde).
        pass # Placeholder for replacement context, using full implementation below

    def stop_safe(self, stop_playlist: bool = True):
        # Gerçek stop mantığı
        if stop_playlist:
            self.is_playlist_mode = False
            self.playlist = []
            
        if self.player:
            try:
                self.player.stop()
                self.player.release()
            except:
                pass
            self.player = None
        self.is_paused = False
        self.current_source = None

    def stop(self, stop_playlist: bool = True):
        """Oynatmayı durdurur"""
        with self.lock:
            self.stop_safe(stop_playlist)

    def pause(self):
        """Oynatmayı duraklatır"""
        with self.lock:
            if self.player and self.is_playing():
                self.player.pause()
                self.is_paused = True
    
    def resume(self):
        """Oynatmayı devam ettirir"""
        with self.lock:
            if self.player and self.is_paused:
                self.player.play()
                self.is_paused = False
    
    def set_volume(self, volume: int):
        """Ses seviyesini ayarlar (0-100)"""
        self.volume = max(0, min(100, volume))
        if self.player:
            # Windows'ta ses seviyesi ek artırım gerekebiliyor (0-255 arası)
            # Linux'ta doğru şekilde 0-100 arasında çalışıyor
            if platform.system() == "Windows":
                # Windows VLC: 0-255 aralığında, 170 = %67, 230 = %90
                # 60 ses seviyesi -> 170 ile 100 olmasını sağla
                adjusted_volume = min(255, int((self.volume / 100) * 255))
                # Minimum 100 (çok kısık sesleri engelle)
                adjusted_volume = max(100, adjusted_volume)
                self.player.audio_set_volume(adjusted_volume)
            else:
                # Linux/Mac: 0-100 aralığında, doğru şekilde çalışıyor
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
        # Müzik kanalı hatası için callback (channel_name, source)
        self.on_music_error: Optional[Callable[[str, Optional[str]], None]] = None
        
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
        Müziği duraklatır, anons bittiğinde devam ettirir
        Zil çalıyorsa zil bitene kadar bekle
        """
        # Zil çalıyorsa bekle
        while self.channels["bell"].is_playing():
            time.sleep(0.1)
        
        with self.lock:
            # Müzik çalıyorsa duraklat (flag'i kontrol et)
            music_was_playing = False
            if self.channels["music"].is_playing() and not self._music_was_playing:
                music_was_playing = True
                self.channels["music"].pause()
            
            # Anonsu çal
            path = self._resolve_path(filename, ANNOUNCEMENTS_DIR)
            success = self.channels["announcement"].play(path)
        
        if blocking and success:
            while self.channels["announcement"].is_playing():
                time.sleep(0.1)
            
            with self.lock:
                # Müziği devam ettir (eğer arka planda çalıyordu)
                if music_was_playing:
                    self.channels["music"].resume()
        
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
                success = self.channels["music"].play(source, is_stream=True)
                # Eğer stream olarak başlatıldıysa, kısa süreli bir monitor başlat
                # (ör: bağlantı hatası ya da hemen kapanma durumunda fallback tetikle)
                if success:
                    def monitor():
                        import time
                        time.sleep(3)
                        try:
                            if not self.channels["music"].is_playing():
                                # Stream başladı ama kısa sürede çalmıyorsa hata say
                                self.handle_channel_error("music", source)
                        except Exception:
                            pass
                    threading.Thread(target=monitor, daemon=True).start()
                return success
            else:
                path = self._resolve_path(source, MUSIC_DIR)
                return self.channels["music"].play(path)

    def play_music_playlist(self, files: list) -> bool:
        """
        Mola müziği playlisti çalar (Her zaman karışık)
        Zil veya anons çalıyorsa başlatmaz
        Zaten müzik çalıyorsa yeni playlist başlatmaz
        """
        if self.channels["bell"].is_playing() or self.channels["announcement"].is_playing():
            return False
        
        # Zaten müzik çalıyorsa yeni playlist başlatma (müzik devam etsin)
        if self.channels["music"].is_playing() and self.channels["music"].is_playlist_mode:
            print("[AudioEngine] Müzik zaten çalıyor, yeni playlist başlatılmıyor")
            return False
            
        # Dosya yollarını tam yola çevir
        full_paths = []
        for f in files:
            path = self._resolve_path(f, MUSIC_DIR)
            if path:
                full_paths.append(path)
        
        if not full_paths:
            print("[AudioEngine] Çalınacak müzik dosyası bulunamadı")
            return False
                
        with self.lock:
            # Mola müziği her zaman karışık çalmalı
            return self.channels["music"].play_playlist(full_paths, shuffle=True)
    
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

    def handle_channel_error(self, channel_name: str, source: Optional[str]):
        """Bir kanal hata verdiğinde çağrılır (ör. medya oynatıcı hata)"""
        try:
            print(f"[AudioEngine] Kanal hata bildirimi: {channel_name} (source={source})")
        except Exception:
            pass

        # Şu an sadece müzik kanalındaki hatalar için özel davranış destekleniyor
        if channel_name == "music":
            try:
                if self.on_music_error:
                    self.on_music_error(channel_name, source)
            except Exception as e:
                print(f"[AudioEngine] on_music_error callback hatası: {e}")
        else:
            # Diğer kanallar için genel logging
            print(f"[AudioEngine] Kanal {channel_name} hata verdi, ek işlem yok")

# Singleton instance
audio_engine = AudioEngine()
