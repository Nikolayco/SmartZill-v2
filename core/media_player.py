"""
NikolayCo SmartZill v2.0 - Medya Player
Manuel müzik kontrolü için bağımsız modül
"""
import vlc
import os
import random
import threading
from pathlib import Path
from typing import Optional, List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import load_config, save_config, MUSIC_DIR


class MediaPlayer:
    """
    Manuel müzik oynatıcı
    - Yerel dosya oynatma
    - İnternet radyosu
    - Playlist yönetimi
    - Bağımsız ses seviyesi
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        
        # VLC instance
        vlc_args = ["--quiet", "--no-video", "--vout=dummy"]
        if sys.platform.startswith("linux"):
            vlc_args.append("--no-xlib")
            
        self.instance = vlc.Instance(*vlc_args)
        self.player: Optional[vlc.MediaPlayer] = None
        
        # Durum
        self.is_paused = False
        self.current_source: Optional[str] = None
        self.current_type: str = "none"  # file, radio, playlist
        
        # Playlist
        self.playlist: List[str] = []
        self.playlist_index: int = 0
        self.shuffle: bool = False
        self.repeat: bool = False
        
        # Ses seviyesi
        config = load_config()
        self.volume = config.get("volumes", {}).get("manual", 70)
        
        # Radyo durumu
        self.radio_url: Optional[str] = None
        self.radio_reconnect_thread: Optional[threading.Thread] = None
        self._stop_reconnect = False
        
        # Dış kontrol için bayrak (zil/anons duraklatması)
        self._external_pause = False
    
    def play_file(self, filepath: str) -> bool:
        """Tek dosya oynatır"""
        with self.lock:
            return self._play_source(filepath, "file")
    
    def play_radio(self, url: str) -> bool:
        """İnternet radyosu oynatır"""
        with self.lock:
            self.radio_url = url
            return self._play_source(url, "radio", is_stream=True)
    
    def play_playlist(self, files: List[str], shuffle: bool = False) -> bool:
        """Playlist oynatır"""
        if not files:
            return False
        
        with self.lock:
            self.playlist = files.copy()
            self.shuffle = shuffle
            self.playlist_index = 0
            
            if shuffle:
                random.shuffle(self.playlist)
            
            return self._play_source(self.playlist[0], "playlist")
    
    def _play_source(self, source: str, source_type: str, is_stream: bool = False) -> bool:
        """Kaynak oynatır"""
        try:
            self.stop()
            
            # YouTube URL kontrolü ve dönüşümü
            if is_stream and ("youtube.com" in source or "youtu.be" in source):
                try:
                    import yt_dlp
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'noplaylist': True,
                        'quiet': True,
                        'no_warnings': True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(source, download=False)
                        if 'url' in info:
                            print(f"[MediaPlayer] YouTube akışı bulundu: {info['title']}")
                            source = info['url']
                except Exception as e:
                    print(f"[MediaPlayer] YouTube çeviri hatası: {e}")
            
            if is_stream:
                media = self.instance.media_new(source)
            else:
                # Dosya yolu çözümle
                if not os.path.isabs(source):
                    source = str(MUSIC_DIR / source)
                
                if not os.path.exists(source):
                    print(f"[MediaPlayer] Dosya bulunamadı: {source}")
                    return False
                
                media = self.instance.media_new_path(source)
            
            self.player = self.instance.media_player_new()
            self.player.set_media(media)
            self.player.audio_set_volume(self.volume)
            
            # Parça bittiğinde callback
            event_manager = self.player.event_manager()
            event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_track_end)
            
            self.player.play()
            self.current_source = source
            self.current_type = source_type
            self.is_paused = False
            self._external_pause = False
            
            return True
            
        except Exception as e:
            print(f"[MediaPlayer] Oynatma hatası: {e}")
            return False
    
    def _on_track_end(self, event):
        """Parça bittiğinde çağrılır"""
        if self.current_type == "playlist":
            self._play_next_in_playlist()
        elif self.current_type == "radio" and self.radio_url:
            # Radyo kopması - yeniden bağlan
            self._start_reconnect()
    
    def _play_next_in_playlist(self):
        """Playlist'te sonraki parçayı oynatır"""
        if not self.playlist:
            return
        
        self.playlist_index += 1
        
        if self.playlist_index >= len(self.playlist):
            if self.repeat:
                self.playlist_index = 0
                if self.shuffle:
                    random.shuffle(self.playlist)
            else:
                self.current_type = "none"
                return
        
        self._play_source(self.playlist[self.playlist_index], "playlist")
    
    def _start_reconnect(self):
        """Radyo yeniden bağlanma thread'i başlatır"""
        if self.radio_reconnect_thread and self.radio_reconnect_thread.is_alive():
            return
        
        self._stop_reconnect = False
        self.radio_reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self.radio_reconnect_thread.start()
    
    def _reconnect_loop(self):
        """Radyo yeniden bağlanma döngüsü"""
        import time
        attempts = 0
        max_attempts = 10
        
        while not self._stop_reconnect and attempts < max_attempts:
            attempts += 1
            print(f"[MediaPlayer] Radyo yeniden bağlanma denemesi {attempts}/{max_attempts}")
            time.sleep(2)
            
            if self._stop_reconnect:
                break
            
            with self.lock:
                if self._play_source(self.radio_url, "radio", is_stream=True):
                    print("[MediaPlayer] Radyo bağlantısı yeniden kuruldu")
                    return
        
        print("[MediaPlayer] Radyo bağlantısı kurulamadı")
    
    def stop(self):
        """Oynatmayı durdurur"""
        self._stop_reconnect = True
        
        if self.player:
            try:
                self.player.stop()
                self.player.release()
            except:
                pass
            self.player = None
        
        self.is_paused = False
        self.current_source = None
        self.current_type = "none"
        self._external_pause = False
    
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
    
    def toggle_play_pause(self):
        """Oynat/Duraklat geçişi"""
        if self.is_paused:
            self.resume()
        elif self.is_playing():
            self.pause()
    
    def external_pause(self):
        """Dış kaynaklı duraklatma (zil/anons)"""
        if self.is_playing():
            self._external_pause = True
            self.pause()
    
    def external_resume(self):
        """Dış kaynaklı duraklatmayı kaldırır"""
        if self._external_pause:
            self._external_pause = False
            self.resume()
    
    def next_track(self):
        """Sonraki parçaya geçer"""
        if self.current_type == "playlist":
            self._play_next_in_playlist()
    
    def previous_track(self):
        """Önceki parçaya geçer"""
        if self.current_type == "playlist" and self.playlist:
            self.playlist_index = max(0, self.playlist_index - 1)
            self._play_source(self.playlist[self.playlist_index], "playlist")
    
    def set_volume(self, volume: int):
        """Ses seviyesini ayarlar (0-100)"""
        self.volume = max(0, min(100, volume))
        if self.player:
            self.player.audio_set_volume(self.volume)
        
        # Yapılandırmaya kaydet
        config = load_config()
        config["volumes"]["manual"] = self.volume
        save_config(config)
    
    def seek(self, position: float):
        """Pozisyona atlar (0.0-1.0)"""
        if self.player and self.current_type == "file":
            self.player.set_position(max(0.0, min(1.0, position)))
    
    def is_playing(self) -> bool:
        """Oynatma durumunu kontrol eder"""
        if not self.player:
            return False
        state = self.player.get_state()
        return state in (vlc.State.Playing, vlc.State.Opening, vlc.State.Buffering)
    
    def get_music_files(self) -> List[dict]:
        """Müzik dizinindeki dosyaları listeler"""
        files = []
        if MUSIC_DIR.exists():
            for f in MUSIC_DIR.iterdir():
                if f.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac", ".m4a"):
                    files.append({
                        "name": f.name,
                        "path": str(f),
                        "size": f.stat().st_size
                    })
        return sorted(files, key=lambda x: x["name"].lower())
    
    def get_status(self) -> dict:
        """Oynatma durumunu döndürür"""
        position = 0.0
        duration = 0
        
        if self.player:
            position = self.player.get_position() or 0.0
            duration = self.player.get_length() or 0
        
        return {
            "playing": self.is_playing(),
            "paused": self.is_paused,
            "external_paused": self._external_pause,
            "volume": self.volume,
            "source": self.current_source,
            "type": self.current_type,
            "position": position,
            "duration": duration,
            "playlist_index": self.playlist_index if self.current_type == "playlist" else -1,
            "playlist_length": len(self.playlist),
            "shuffle": self.shuffle,
            "repeat": self.repeat
        }


# Singleton instance
media_player = MediaPlayer()
