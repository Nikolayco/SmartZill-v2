# 🎵 NikolayCo SmartZill v2.0 - Automated Bell & Music Scheduler

**NikolayCo SmartZill**, işyerleri, okullar ve ofisler için tasarlanmış modern, kapsamlı ve kullanıcı dostu bir **otomasyon sistemidir**. **Zilleri**, **anonsları** ve **müzik yayınlarını** tam otomatik bir şekilde yönetmenizi sağlar. Web arayüzü sayesinde yerel ağ üzerinden istenilen cihazdan kontrol edilebilir.


<img width="1919" height="792" alt="image" src="https://github.com/user-attachments/assets/b0507998-f557-451d-bcfa-7c75d1228646" />


<img width="1917" height="607" alt="image" src="https://github.com/user-attachments/assets/56806197-b7e8-4f5c-8474-7b554a785689" />


<img width="1914" height="683" alt="image" src="https://github.com/user-attachments/assets/0296d228-20a8-4365-b2b8-4f9275ee1a09" />


<img width="1912" height="912" alt="image" src="https://github.com/user-attachments/assets/9b92279e-1084-42af-aeba-2a96014f235f" />


<img width="1916" height="691" alt="image" src="https://github.com/user-attachments/assets/44ecf769-7898-426e-baed-529c35d507e3" />


---

## 🇹🇷 Türkçe (Turkish)

### 🌟 Öne Çıkan Özellikler

*   **Modern Web Arayüzü:** Yönetimi kolay, sürükle-bırak destekli, tüm cihazlarla uyumlu (Mobil/Tablet/PC) HTML5/CSS3 arayüz.
*   **Haftalık Akıllı Zamanlayıcı:** Her gün için farklı ders, mola, mesai başlangıç/bitiş saatleri ayarlama. Kopyala/Yapıştır özelliği ile hızlı programlama.
*   **Akıllı Müzik ve Radyo Yayını:**
    *   **Mola Müzikleri:** Mola saatlerinde belirlediğiniz klasörden otomatik müzik çalar. Mesai başladığında otomatik fade-out (yavaşça kısarak) ile durur.
    *   **Canlı Radyo:** Yerel MP3'ler yerine favori internet radyolarınızı dinletme imkanı. Kopma durumunda otomatik yeniden bağlanma özelliği.
    *   **Smart Start:** Uygulama açıldığında o anki saati kontrol eder; eğer mola saatindeyse müziği başlatır, değilse sessiz bekler.
*   **Gelişmiş Sesli Anons (TTS):**
    *   **Yapay Zeka Destekli Sesler:** Microsoft Edge TTS altyapısı ile metinlerinizi **doğal insan sesi** kalitesinde (Türkçe ve 4+ dil) anons eder.
    *   **3 Farklı Zamanlı Duyuru:** Günlük 3 farklı saatte planlanmış otomatik duyuru yapabilme.
    *   **Anlık Duyuru:** Yazdığınız metni anında tüm sisteme okuma.
*   **Özel Günler ve Doğum Günleri:**
    *   **Otomatik Kutlama:** Yüklenen personel listesinden (Excel/CSV) doğum günlerini takip eder ve belirlediğiniz saatte otomatik kutlama anonsu yapar.
    *   **Şablon İndirme:** Kolay veri girişi için hazır Excel şablonu.
*   **Resmi Tatil Modu:** Türkiye (veya seçilen ülke) resmi tatillerini otomatik algılar ve sistemi o günlerde sessize alır.
*   **Sistem Yönetimi:**
    *   **Kanal Bazlı Ses Kontrolü:** Zil, Müzik, Anons ses seviyelerini ayrı ayrı ayarlama.
    *   **Yedekleme:** Tüm ayarları tek tıkla JSON veya Excel olarak yedekleme ve geri yükleme.
    *   **Linux/Windows Desteği:** Her iki işletim sisteminde de sorunsuz çalışma ve başlangıçta otomatik açılma.

### 🛡️ Güvenlik ve Şeffaflık Bildirimi (Security Transparency)

Kurumsal ağ yöneticileri ve güvenlik ekipleri için teknik detaylar:
*   **Ağ (Network) Aktiviteleri:** Uygulama, **sadece** aşağıdaki durumlar için internete bağlanır:
    *   **İnternet Radyosu:** Kullanıcının eklediği radyo istasyonlarını çalmak için.
    *   **Kurulum:** Gerekli Python kütüphanelerini (`pip`) indirmek için.
    *   **VLC İndirme:** Windows'ta VLC yüklü değilse, VideoLAN resmi sitesinden "portable" sürümü indirir.
    *   **Veri Gizliliği:** Dışarıya hiçbir kullanım istatistiği, ses kaydı veya personel verisi gönderilmez. Tüm veriler yerel diskte saklanır.
*   **Dosya Sistemi:** Uygulama kendi klasörü (`.venv` ve `bin/`) dışında sistem dosyalarında değişiklik yapmaz.

### 📋 Gereksinimler (Prerequisites)

Bu uygulamanın çalışması için sisteminizde aşağıdaki bileşenlerin yüklü olması gerekmektedir:

1.  **Python 3.10 veya üzeri**: Yüklü değilse [python.org](https://www.python.org/) adresinden indirin.
2.  **VLC Media Player**: Ses çalma motoru için gereklidir.
    *   **Linux:** `sudo apt install vlc`
    *   **Windows:** Başlangıç scripti otomatik kurmayı dener, ancak manuel kurulum önerilir.
3.  **FFmpeg**: Radyo ve YT yayınları için önerilir.
    *   **Linux:** `sudo apt install ffmpeg`
    *   **Windows:** [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/) adresinden indirip PATH'e ekleyin (Opsiyonel).

### 🚀 Hızlı Kurulum


#### 🐧 Linux (Önerilen)
```bash
# 1. Projeyi İndir
git clone https://github.com/Nikolayco/SmartZill-v2.git
cd SmartZill-v2

# 2. Çalıştır
# Script gerekli tüm kurulumları (Python, kütüphaneler) otomatik yapar.
chmod +x run_linux.sh
./run_linux.sh
```

#### 🪟 Windows (Adım Adım)
**Yönetici Olarak (Run as Administrator)** başlatmanız önerilir.

1. **Yöntem 1 (Git ile):**
   ```cmd
   git clone https://github.com/Nikolayco/SmartZill-v2.git
   cd SmartZill-v2
   run_windows.bat
   ```

2. **Yöntem 2 (ZIP ile):**
   - Sağ üstteki yeşil **Code** butonundan **Download ZIP** seçeneği ile indirin.
   - Klasöre çıkartın.
   - `run_windows.bat` dosyasına sağ tıklayıp **Yönetici Olarak Çalıştır** deyin.

### 🔑 Varsayılan Giriş Bilgileri (Default Login)
*   **Kullanıcı Adı:** (Gerekmez / Not Required)
*   **Şifre:** `admin` (İlk kurulumda)
    *   *Güvenliğiniz için kurulumdan sonra ayarlardan değiştiriniz.*

---

## 🇬🇧 English


### 🌟 Key Features

*   **Modern Web Interface:** Easy-to-use, responsive HTML5/CSS3 interface compatible with all devices.
*   **Smart Weekly Scheduler:** Program different schedules for each day. Copy/Paste days for quick setup.
*   **Smart Music & Radio:**
    *   **Break Music:** Auto-plays local music during breaks with fade-out effect.
    *   **Live Radio:** Stream internet radio stations robustly with auto-reconnect.
    *   **Smart Start:** Checks current time on startup; plays music if it's break time.
*   **Advanced TTS (Text-to-Speech):**
    *   **AI-Powered Voices:** Converts text to **Natural Human Speech** using Edge TTS engine.
    *   **Scheduled Announcements:** Plan announcements for 3 different times daily.
*   **Birthdays & Special Days:**
    *   **Auto-Celebration:** Imports personnel lists (Excel) and automatically announces birthdays.
    *   **Public Holidays:** Auto-fetches holidays and mutes the system.
*   **System Management:**
    *   **Individual Volume Control:** Separate volume controls for Bells, Music, and Announcements.
    *   **Backup & Restore:** Export full configuration to JSON/Excel.

### 🛡️ Security & Transparency Note

To assure security teams and admins, here is what the application does under the hood:
*   **Network Activity:** The app makes outbound calls **only** for:
    *   **Internet Radio:** Connecting to the streaming URLs you provide.
    *   **Setup:** Downloading necessary Python packages (`pip`) or the portable VLC player if missing.
    *   **No Telemetry:** No personal data or usage analytics are sent to external servers.
*   **File System:** It runs within its own directory. On Windows, if VLC is missing, it downloads a portable version to a local `bin/` folder to avoid requiring system-wide installation privileges.

---

**Project Owner:** NikolayCo  
**License:** MIT

