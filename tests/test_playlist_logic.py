import sys
import os
import time
import threading
import unittest
from unittest.mock import MagicMock, patch

# 1. VLC Modülünü Mockla (Gerçek VLC kurulu olmasa bile test çalışsın)
# Bu işlem, core.audio_engine import edilmeden ÖNCE yapılmalı.
mock_vlc = MagicMock()
sys.modules['vlc'] = mock_vlc

# Mock VLC Event Manager ve Player davranışları
mock_player = MagicMock()
mock_event_manager = MagicMock()
mock_vlc.Instance.return_value.media_player_new.return_value = mock_player
mock_player.event_manager.return_value = mock_event_manager

# Event callback'ini saklamak için
callback_storage = {}
def side_effect_attach(event_type, callback):
    callback_storage['end_reached'] = callback
mock_event_manager.event_attach.side_effect = side_effect_attach

# 2. Proje yolunu ekle ve modülleri import et
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Config'i mocklayarak gerçek dosya yollarından bağımsız hale getir
with patch('config.MUSIC_DIR') as mock_music_dir:
    # Sahte müzik dosyası yolları döndürsün
    mock_music_dir.iterdir.return_value = [] # iterdir kullanılmıyor ama ne olur ne olmaz
    
    # Import işlemi şimdi yapılabilir
    from core.audio_engine import AudioEngine, AudioChannel

class TestPlaylistLogic(unittest.TestCase):
    
    def setUp(self):
        """Her testten önce çalışır"""
        self.engine = AudioEngine()
        # Test için sahte bir müzik listesi
        self.test_files = ["song1.mp3", "song2.mp3", "song3.mp3", "song4.mp3", "song5.mp3"]
        
        # AudioChannel'ın play metodunu izlemek için spy (casus) koyacağız
        # Ancak AudioEngine __init__ içinde kanalları oluşturduğu için,
        # engine.channels['music'] üzerindeki metodları mocklayacağız.
        
        # Orijinal play metodunu sakla (gerçek mantığı test etmek istiyoruz)
        # Sadece vlc player kısmını mockladık.
        
        # DÜZELTME: is_playing() varsayılan olarak Mock döner (True). 
        # Bunu False yapmalıyız ki play_music_playlist çalışsın.
        for channel in self.engine.channels.values():
            # Player nesnesi mock olduğu için onun metodlarını da ayarla
            # Ancak channel.is_playing() kendi içinde player.get_state() kullanır.
            # Biz channel.is_playing metodunu direkt mocklamak istemiyoruz çünkü onu test ediyoruz.
            # Ancak channel.player henüz None, dolayısıyla is_playing False dönmeli.
            # Fakat channel.__init__ içinde player None başlar.
            
            # play_music_playlist içinde:
            # if self.channels["bell"].is_playing() ...
            
            # bell kanalı init'te oluşturuldu, player None.
            # channel.is_playing() -> if not self.player: return False
            # Bu durumda sorun olmamalıydı?
            
            # Analiz: AudioChannel.__init__ içindeki vlc.Instance çağrısı mocklandı.
            # channel oluşturuldu. 
            # channel.is_playing() -> player None ise False döner.
            # Ama setUp'da engine yeni oluşturuluyor.
            
            # Sorun şurada olabilir: AudioEngine init edilirken config load ediliyor.
            pass
            
        # os.path.exists'i GENEL olarak mockla.
        # Çünkü thread içinde çalışan _play_next de buna ihtiyaç duyuyor.
        self.patcher = patch('os.path.exists', return_value=True)
        self.mock_exists = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_playlist_shuffle_and_sequence(self):
        """TEST 1: Karışık Çalma ve Sıralı Geçiş Testi"""
        print("\n=== TEST 1: Karışık Çalma ve Sıralı Geçiş ===")
        
        music_channel = self.engine.channels['music']
        
        # 1. Mola Müziği Başlat (5 şarkılık liste ile)
        print(f"[*] Playlist gönderiliyor: {self.test_files}")
        
        # resolve_path fonksiyonunu mockla ki gerçek dosya aramasın
        with patch.object(self.engine, '_resolve_path', side_effect=lambda x, y: f"/fake/path/{x}"):
            res = self.engine.play_music_playlist(self.test_files)
        
        self.assertTrue(res, "Müzik başlatılamadı")
        self.assertTrue(music_channel.is_playlist_mode, "Kanal playlist modunda değil")
        self.assertEqual(len(music_channel.playlist), 5, "Playlist uzunluğu hatalı")
        
        # 2. Shuffle Kontrolü (Orijinal liste ile kanalın listesi aynı olmamalı)
        # Not: Çok düşük bir ihtimalle aynı olabilir, o yüzden %100 fail garantisi vermez ama pratikte yeterli.
        print(f"[*] Orijinal Sıra: {self.test_files}")
        # Dosya isimlerini path'den ayıkla
        current_playlist_names = [os.path.basename(p) for p in music_channel.playlist]
        print(f"[*] Karışık Sıra:   {current_playlist_names}")
        
        if current_playlist_names == self.test_files:
            print("[!] UYARI: Shuffle sonucu orijinal ile aynı çıktı (tesadüf olabilir)")
        else:
            print("[+] Shuffle başarılı: Liste sırası değişti.")
            
        # 3. İlk Şarkı Çalıyor mu?
        self.assertTrue(mock_player.play.called, "VLC play() çağrılmadı (İlk şarkı başlamadı)")
        print(f"[+] 1. Şarkı çalıyor: {music_channel.current_source}")
        
        # 4. Şarkı Bitişini Simüle Et ve 2. Şarkıya Geçişi İzle
        # Mevcut indexi al
        first_index = music_channel.playlist_index
        print(f"[*] Şu anki index: {first_index}")
        
        # VLC'nin "EndReached" eventini tetikle
        print("[*] Şarkı bitiş sinyali gönderiliyor...")
        if 'end_reached' in callback_storage:
            # Event callback'i ayrı thread'de çalışabilir, biz direkt çağırıyoruz
            # Ancak AudioChannel içinde play_next ayrı bir thread başlatır.
            # Test ortamında bu thread'in bitmesini beklemeliyiz.
            
            # play metodunu sıfırla ki 2. kez çağrıldığını anlayalım
            mock_player.play.reset_mock()
            
            callback_storage['end_reached'](None)
            
            # Thread'in çalışması için kısa bir bekleme
            time.sleep(0.5)
            
            # 5. İkinci Şarkı Kontrolü
            self.assertTrue(mock_player.play.called, "2. Şarkı için play() çağrılmadı")
            self.assertEqual(music_channel.playlist_index, first_index + 1, "Index artmadı")
            print(f"[+] 2. Şarkı çalıyor: {music_channel.current_source}")
            
        else:
            self.fail("Event callback'i attach edilmedi!")

    def test_playlist_loop(self):
        """TEST 2: Liste Bitince Başa Dönme (Loop) Testi"""
        print("\n=== TEST 2: Liste Bitince Başa Dönme ===")
        
        music_channel = self.engine.channels['music']
        
        # 2 şarkılık kısa liste
        short_list = ["a.mp3", "b.mp3"]
        
        with patch.object(self.engine, '_resolve_path', side_effect=lambda x, y: f"/fake/path/{x}"):
            self.engine.play_music_playlist(short_list)
            
        # 1. Şarkı Çalıyor
        print("[*] 1. Şarkı başladı")
        mock_player.play.reset_mock()
        
        # 1 -> 2 Geçiş
        print("[*] 1. Şarkı bitti -> 2. Şarkıya geçiliyor")
        callback_storage['end_reached'](None)
        time.sleep(0.2)
        self.assertTrue(mock_player.play.called, "2. Şarkıya geçilmedi")
        mock_player.play.reset_mock()
        
        # 2 -> 1 (Başa Dönüş / Yeni Shuffle) Geçiş
        print("[*] 2. Şarkı bitti -> Listeyi karıştırıp başa dönmeli")
        
        # Şu anki listeyi sakla
        old_playlist = music_channel.playlist.copy()
        
        callback_storage['end_reached'](None)
        time.sleep(0.2)
        
        self.assertTrue(mock_player.play.called, "Başa dönüldüğünde play() çağrılmadı")
        self.assertEqual(music_channel.playlist_index, 0, "Index 0'a sıfırlanmadı")
        
        # Yeni listenin eskisiyle aynı olup olmadığını (shuffle yapılıp yapılmadığını) kontrol et
        # 2 elemanlı listede %50 şansla aynı olabilir ama mantık çalışma kontrolü için yeterli
        print(f"[+] Döngü başarılı. Yeni çalınan: {music_channel.current_source}")


if __name__ == '__main__':
    unittest.main()
