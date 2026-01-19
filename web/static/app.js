/**
 * NikolayCo SmartZill v2.0 - Frontend JavaScript
 * Tam özellikli, debounce, öncelik sistemi
 */

const API = '';

// State
let schedule = [];
let selectedDay = 0;
let currentCategory = 'bells';
let copiedDay = null;
let editingActivity = null;
let nextEvent = null;
let radioStations = [];
let birthdaySortBy = 'date';  // Varsayılan olarak tarihe göre sırala
let isProcessing = {};
let isAudioPlaying = false;  // Ses çalıyor mu?
let confirmCallback = null;

// Tüm ülkeler - alfabetik sıralı
const ALL_COUNTRIES = [
    { code: 'US', name: 'ABD 🇺🇸' },
    { code: 'DE', name: 'Almanya 🇩🇪' },
    { code: 'AR', name: 'Arjantin 🇦🇷' },
    { code: 'AU', name: 'Avustralya 🇦🇺' },
    { code: 'AT', name: 'Avusturya 🇦🇹' },
    { code: 'AE', name: 'BAE 🇦🇪' },
    { code: 'BE', name: 'Belçika 🇧🇪' },
    { code: 'BR', name: 'Brezilya 🇧🇷' },
    { code: 'BG', name: 'Bulgaristan 🇧🇬' },
    { code: 'CZ', name: 'Çekya 🇨🇿' },
    { code: 'CN', name: 'Çin 🇨🇳' },
    { code: 'DK', name: 'Danimarka 🇩🇰' },
    { code: 'FI', name: 'Finlandiya 🇫🇮' },
    { code: 'FR', name: 'Fransa 🇫🇷' },
    { code: 'ZA', name: 'G. Afrika 🇿🇦' },
    { code: 'KR', name: 'Güney Kore 🇰🇷' },
    { code: 'IN', name: 'Hindistan 🇮🇳' },
    { code: 'NL', name: 'Hollanda 🇳🇱' },
    { code: 'GB', name: 'İngiltere 🇬🇧' },
    { code: 'IE', name: 'İrlanda 🇮🇪' },
    { code: 'ES', name: 'İspanya 🇪🇸' },
    { code: 'SE', name: 'İsveç 🇸🇪' },
    { code: 'CH', name: 'İsviçre 🇨🇭' },
    { code: 'IL', name: 'İsrail 🇮🇱' },
    { code: 'IT', name: 'İtalya 🇮🇹' },
    { code: 'JP', name: 'Japonya 🇯🇵' },
    { code: 'CA', name: 'Kanada 🇨🇦' },
    { code: 'HU', name: 'Macaristan 🇭🇺' },
    { code: 'MX', name: 'Meksika 🇲🇽' },
    { code: 'EG', name: 'Mısır 🇪🇬' },
    { code: 'NO', name: 'Norveç 🇳🇴' },
    { code: 'PL', name: 'Polonya 🇵🇱' },
    { code: 'PT', name: 'Portekiz 🇵🇹' },
    { code: 'RO', name: 'Romanya 🇷🇴' },
    { code: 'RU', name: 'Rusya 🇷🇺' },
    { code: 'SA', name: 'S. Arabistan 🇸🇦' },
    { code: 'TR', name: 'Türkiye 🇹🇷' },
    { code: 'UA', name: 'Ukrayna 🇺🇦' },
    { code: 'NZ', name: 'Yeni Zelanda 🇳🇿' },
    { code: 'GR', name: 'Yunanistan 🇬🇷' }
];

// Debounce - çift tıklamayı engeller
async function withDebounce(btnId, fn, delay = 2000) {
    if (isProcessing[btnId]) {
        console.log(`Button ${btnId} is already processing`);
        return;
    }

    isProcessing[btnId] = true;

    const btn = document.getElementById(btnId);
    if (btn) {
        btn.disabled = true;
        btn.style.opacity = '0.5';
    }

    try {
        await fn();
    } catch (error) {
        console.error(`Error in ${btnId}:`, error);
    } finally {
        setTimeout(() => {
            isProcessing[btnId] = false;
            if (btn) {
                btn.disabled = false;
                btn.style.opacity = '1';
            }
        }, delay);
    }
}


// ===== CUSTOM MODALS =====

function customAlert(message, title = 'Bilgi') {
    document.getElementById('alert-title').textContent = title;
    document.getElementById('alert-message').textContent = message;
    document.getElementById('custom-alert-modal').classList.add('open');
}

function customConfirm(message, title = 'Onay') {
    return new Promise((resolve) => {
        document.getElementById('confirm-title').textContent = title;
        document.getElementById('confirm-message').textContent = message;
        document.getElementById('custom-confirm-modal').classList.add('open');
        confirmCallback = resolve;
    });
}

function closeCustomConfirm(result) {
    document.getElementById('custom-confirm-modal').classList.remove('open');
    if (confirmCallback) {
        confirmCallback(result);
        confirmCallback = null;
    }
}

// Override global alert and confirm
window.alert = customAlert;
window.confirm = customConfirm;

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initClock();
    initUploadZones();
    initCountrySelect();
    loadInitialData();
    startPolling();
    loadCompanyName();
    loadAdSenseCode();

    // Auto-refresh every 5 minutes to prevent crashes
    setInterval(() => {
        console.log('Auto-refreshing page to prevent crashes...');
        location.reload();
    }, 5 * 60 * 1000); // 5 minutes
});

function initUploadZones() {
    document.querySelectorAll('.upload-zone-mini').forEach(zone => {
        const input = zone.querySelector('input[type="file"]');
        const category = zone.dataset.category;

        if (!input || !category) return;

        // Click to upload
        zone.addEventListener('click', () => input.click());

        // Drag and drop
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.style.borderColor = 'var(--accent)';
            zone.style.background = 'rgba(108, 92, 231, 0.1)';
        });

        zone.addEventListener('dragleave', () => {
            zone.style.borderColor = '';
            zone.style.background = '';
        });

        zone.addEventListener('drop', async (e) => {
            e.preventDefault();
            zone.style.borderColor = '';
            zone.style.background = '';
            await uploadSoundFiles(category, e.dataTransfer.files);
        });

        // File input change
        input.addEventListener('change', async () => {
            if (input.files.length > 0) {
                await uploadSoundFiles(category, input.files);
                input.value = ''; // Reset
            }
        });
    });
}

async function uploadSoundFiles(category, files) {
    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file);
    }

    try {
        const res = await fetch(`/api/sounds/${category}/upload`, {
            method: 'POST',
            body: formData
        });

        if (res.ok) {
            customAlert(`${files.length} dosya başarıyla yüklendi!`, 'Başarılı');
            loadSoundsFor(category);
        } else {
            customAlert('Dosya yükleme başarısız oldu.', 'Hata');
        }
    } catch (e) {
        customAlert('Dosya yükleme sırasında hata oluştu.', 'Hata');
    }
}


function initNavigation() {
    console.log('[Navigation] Initializing...');
    const navButtons = document.querySelectorAll('.nav-btn');
    console.log(`[Navigation] Found ${navButtons.length} navigation buttons`);

    navButtons.forEach(btn => {
        const page = btn.dataset.page;
        console.log(`[Navigation] Attaching listener to button: ${page}`);
        btn.addEventListener('click', () => {
            console.log(`[Navigation] Button clicked: ${page}`);
            showPage(page);
        });
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const cat = btn.dataset.category;
            if (cat) {
                currentCategory = cat;
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                loadSounds(cat);
            }
        });
    });
    console.log('[Navigation] Initialization complete');
}

function showPage(page) {
    console.log(`[showPage] Switching to page: ${page}`);
    document.querySelectorAll('.nav-btn').forEach(b =>
        b.classList.toggle('active', b.dataset.page === page));
    document.querySelectorAll('.page').forEach(p =>
        p.classList.toggle('active', p.id === `page-${page}`));

    if (page === 'scheduler') loadSchedule();
    if (page === 'media') { loadMediaFiles(); loadRadioStations(); }
    if (page === 'sounds') {
        // Tüm kategorileri yükle
        loadSounds('bells');
        loadSounds('announcements');
        loadSounds('music');
    }
    if (page === 'special') loadSpecialDays();
    if (page === 'settings') loadSettings();
    if (page === 'ads') {
        // Bir şey yapmaya gerek yok, varsayılan olarak login formu gelir
        document.getElementById('admin-password').focus();
    }
    console.log(`[showPage] Page switch complete: ${page}`);
}

function initClock() {
    function update() {
        const now = new Date();
        const time = now.toLocaleTimeString('tr-TR');
        const date = now.toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' });

        const clockEl = document.getElementById('clock');
        const dateEl = document.getElementById('date');
        const dbClockEl = document.getElementById('db-clock');
        const dbDateEl = document.getElementById('db-date');

        if (clockEl) clockEl.textContent = time;
        if (dateEl) dateEl.textContent = date;
        if (dbClockEl) dbClockEl.textContent = time;
        if (dbDateEl) dbDateEl.textContent = date;

        updateCountdown();
    }
    update();
    setInterval(update, 1000);
}

function updateCountdown() {
    if (!nextEvent) return;

    const now = new Date();
    const [h, m] = nextEvent.time.split(':').map(Number);
    const eventTime = new Date();
    eventTime.setHours(h, m, 0, 0);
    if (eventTime < now) eventTime.setDate(eventTime.getDate() + 1);

    const diff = eventTime - now;
    const hours = Math.floor(diff / 3600000);
    const mins = Math.floor((diff % 3600000) / 60000);
    const secs = Math.floor((diff % 60000) / 1000);

    const hEl = document.getElementById('countdown-hours');
    const mEl = document.getElementById('countdown-mins');
    const sEl = document.getElementById('countdown-secs');
    if (hEl) hEl.textContent = hours.toString().padStart(2, '0');
    if (mEl) mEl.textContent = mins.toString().padStart(2, '0');
    if (sEl) sEl.textContent = secs.toString().padStart(2, '0');
}

function initUploadZone() {
    const zone = document.getElementById('upload-zone');
    const input = document.getElementById('file-input');
    if (!zone || !input) return;

    zone.onclick = () => input.click();
    zone.ondragover = e => { e.preventDefault(); zone.style.borderColor = 'var(--accent)'; };
    zone.ondragleave = () => zone.style.borderColor = 'var(--border)';
    zone.ondrop = async e => {
        e.preventDefault();
        zone.style.borderColor = 'var(--border)';
        await uploadFiles(e.dataTransfer.files);
    };
    input.onchange = async () => { await uploadFiles(input.files); input.value = ''; };
}

function initCountrySelect() {
    const select = document.getElementById('holiday-country');
    if (!select) return;
    select.innerHTML = ALL_COUNTRIES.map(c =>
        `<option value="${c.code}">${c.name}</option>`
    ).join('');
}

async function loadInitialData() {
    await loadStatus();
    await loadTimeline();
    await loadTVGuide();
    await loadVolumes();
}

function startPolling() {
    setInterval(loadStatus, 2000);
    setInterval(loadTimeline, 30000);
    setInterval(loadTVGuide, 30000);
}

// ===== API =====

async function api(endpoint, options = {}) {
    try {
        const res = await fetch(API + endpoint, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        if (!res.ok) throw new Error(res.statusText);
        return await res.json();
    } catch (e) {
        console.error('API:', e);
        return null;
    }
}

// ===== STATUS =====

async function loadStatus() {
    const s = await api('/api/status');
    if (!s) return;

    // Scheduler toggle button
    const toggleBtn = document.getElementById('scheduler-toggle-btn');
    const toggleIcon = document.getElementById('scheduler-toggle-icon');
    const isSchedulerRunning = s.scheduler?.running;

    if (toggleBtn && toggleIcon) {
        if (isSchedulerRunning) {
            toggleBtn.classList.remove('inactive');
            toggleIcon.textContent = '⚡';
            toggleBtn.title = 'Geçici olarak pasif yap (tüm otomatik işlemler durur)';
        } else {
            toggleBtn.classList.add('inactive');
            toggleIcon.textContent = '⏸️';
            toggleBtn.title = 'Tekrar aktif et';
        }
    }

    // Next event
    nextEvent = s.scheduler?.next_event;
    const ntEl = document.getElementById('next-time');
    const nnEl = document.getElementById('next-name');
    if (nextEvent) {
        if (ntEl) ntEl.textContent = nextEvent.time;
        if (nnEl) nnEl.textContent = `${nextEvent.name} (${nextEvent.type === 'start' ? 'Başlangıç' : 'Bitiş'})`;
    } else {
        if (ntEl) ntEl.textContent = '--:--';
        if (nnEl) nnEl.textContent = 'Bugün etkinlik yok';
    }

    // Holiday
    const holEl = document.getElementById('holiday-status');
    if (holEl) holEl.textContent = s.holidays?.is_holiday ? `🎉 ${s.holidays.holiday_name}` : '✅ Çalışma Günü';

    // System status - more descriptive messages
    const audio = s.audio || {};
    const media = s.media_player || {};
    let np = 'İşlem bekleniyor...';

    // Global ses durumu - çakışmayı önlemek için
    isAudioPlaying = audio.bell?.playing || audio.announcement?.playing ||
        audio.music?.playing || media.playing;

    if (audio.bell?.playing) np = '🔔 Zil çalıyor';
    else if (audio.announcement?.playing) np = '📢 Anons yapılıyor';
    else if (audio.music?.playing) np = '🎵 Mola müziği çalıyor';
    else if (media.playing) np = '🎧 ' + getDisplayName(media.source);
    else if (!isSchedulerRunning) np = '⏸️ Zamanlayıcı kapalı';

    const npEl = document.getElementById('now-playing');
    if (npEl) npEl.textContent = np;

    // Manual music status
    const mmEl = document.getElementById('manual-music-status');
    if (mmEl) {
        if (media.playing) mmEl.textContent = '▶️ Çalıyor';
        else if (media.paused) mmEl.textContent = '⏸️ Duraklatıldı';
        else mmEl.textContent = 'Kapalı';
    }

    // Media player display
    const mpnEl = document.getElementById('media-now-playing');
    const mpsEl = document.getElementById('media-source');
    const mpEl = document.getElementById('media-progress');
    const ppBtn = document.getElementById('play-pause-btn');

    if (mpnEl) mpnEl.textContent = media.playing || media.paused ? getDisplayName(media.source) : 'Çalınmıyor';
    if (mpsEl) mpsEl.textContent = media.source?.startsWith('http') ? '📻 Radyo' : '📁 Yerel dosya';
    if (mpEl) mpEl.style.width = `${(media.position || 0) * 100}%`;
    if (ppBtn) ppBtn.textContent = media.paused ? '▶️' : (media.playing ? '⏸️' : '▶️');
}

function getDisplayName(source) {
    if (!source) return 'Bilinmiyor';

    // Radyo URL'lerinden isim çıkar
    if (source.includes('radyo34')) return 'Radyo 34';
    if (source.includes('kralfm')) return 'Kral FM';
    if (source.includes('powerturk')) return 'Power Türk';
    if (source.includes('showradyo')) return 'Show Radyo';
    if (source.includes('youtube')) return 'YouTube';

    // Dosya adını al
    const name = source.split('/').pop().split('?')[0];
    if (name.includes('.mp3') || name.includes('.m3u8') || name.includes('.aac')) {
        return name.replace(/\.(mp3|m3u8|aac|stream)$/i, '').replace(/[_;]/g, ' ');
    }

    // Son çare: kısalt
    if (name.length > 30) return name.substring(0, 30) + '...';
    return name;
}

async function loadTimeline() {
    const timeline = await api('/api/schedule/timeline');
    const container = document.getElementById('timeline');
    if (!container) return;

    if (!timeline?.length) {
        container.innerHTML = '<p style="color:var(--text-secondary);text-align:center;padding:2rem">Bugün etkinlik yok</p>';
        return;
    }

    // Aktivite sayacı
    let activityCounter = {};

    // Şu anki zamanı bul (en yakın aktivite için)
    const now = new Date();
    const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    let nextActivityIndex = timeline.findIndex(t => t.time >= currentTime);
    if (nextActivityIndex === -1) nextActivityIndex = 0; // Hepsi geçmişse ilkini vurgula

    container.innerHTML = timeline.map((t, index) => {
        // Aktivite numarasını bul
        if (!activityCounter[t.name]) {
            activityCounter[t.name] = Object.keys(activityCounter).length + 1;
        }
        const actNum = activityCounter[t.name];

        // Açıklayıcı label oluştur
        let label = '';
        if (t.type === 'start') {
            label = `${actNum}. Aktivite Başlangıç`;
        } else if (t.type === 'end') {
            label = `${actNum}. Aktivite Bitiş`;
        } else if (t.type === 'announcement') {
            label = `${actNum}. Aktivite Duyuru`;
        }

        const icon = t.type === 'start' ? '▶' : t.type === 'end' ? '■' : '📢';

        // En yakın aktiviteyi vurgula
        const isNext = index === nextActivityIndex;
        const highlightClass = isNext ? 'next-activity' : '';

        return `
        <div class="timeline-item ${t.type} ${highlightClass}">
            <span class="timeline-time">${t.time}</span>
            <span class="timeline-label">${label}</span>
            <span style="margin-left:auto;opacity:0.7">${icon}</span>
        </div>
    `}).join('');
}

async function loadTVGuide() {
    console.log('[TVGuide] Loading...');
    const schedule = await api('/api/schedule/today');
    console.log('[TVGuide] Schedule data:', schedule);

    const container = document.getElementById('tv-guide-timeline');
    if (!container) {
        console.error('[TVGuide] Container not found!');
        return;
    }

    const activities = schedule?.activities || [];
    console.log(`[TVGuide] Found ${activities.length} activities`);

    if (!activities.length) {
        container.innerHTML = '<div class="tv-guide-empty">📺 Bugün için program yok</div>';
        console.log('[TVGuide] No activities, showing empty message');
        return;
    }

    // Şu anki zamanı bul
    const now = new Date();
    const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    console.log(`[TVGuide] Current time: ${currentTime}`);

    container.innerHTML = activities.map(activity => {
        const startTime = activity.startTime || '';
        const endTime = activity.endTime || '';
        const name = activity.name || 'İsimsiz Etkinlik';

        // Süre hesapla (saat ve dakika olarak)
        let duration = '';
        if (startTime && endTime) {
            const [startH, startM] = startTime.split(':').map(Number);
            const [endH, endM] = endTime.split(':').map(Number);
            const durationMins = (endH * 60 + endM) - (startH * 60 + startM);

            const hours = Math.floor(durationMins / 60);
            const mins = durationMins % 60;

            if (hours > 0 && mins > 0) {
                duration = `${hours}sa. ${mins}dk.`;
            } else if (hours > 0) {
                duration = `${hours}sa.`;
            } else {
                duration = `${mins}dk.`;
            }
        }

        // Aktif mi kontrol et
        const isActive = startTime <= currentTime && currentTime < endTime;
        const activeClass = isActive ? 'active' : '';

        return `
        <div class="tv-guide-item ${activeClass}">
            <div class="tv-guide-time">${startTime} - ${endTime}</div>
            <div class="tv-guide-name">${name}</div>
            <div class="tv-guide-duration">${duration}</div>
        </div>
        `;
    }).join('');

    console.log(`[TVGuide] Rendered ${activities.length} activities successfully`);
}

// ===== CONTROLS =====

async function playBell() {
    console.log('playBell called');
    try {
        await withDebounce('btn-bell', async () => {
            console.log('Playing bell...');
            const result = await api('/api/bell/play?filename=default.mp3', { method: 'POST' });
            console.log('Bell result:', result);
            return result;
        }, 3000);
    } catch (error) {
        console.error('playBell error:', error);
    }
}

async function stopAll() {
    console.log('stopAll called');
    try {
        await withDebounce('btn-stop', async () => {
            console.log('Stopping all...');
            const result = await api('/api/stop', { method: 'POST' });
            console.log('Stop result:', result);
            return result;
        }, 1000);
    } catch (error) {
        console.error('stopAll error:', error);
    }
}

async function stopAnnouncement() {
    withDebounce('btn-tts-stop', () => api('/api/stop', { method: 'POST' }), 1000);
}

async function playTTS() {
    const text = document.getElementById('tts-input')?.value?.trim();
    if (!text) {
        customAlert('Lütfen bir metin girin.', 'Uyarı');
        return;
    }

    withDebounce('btn-tts-play', async () => {
        try {
            const result = await api('/api/tts', {
                method: 'POST',
                body: JSON.stringify({ text, language: 'tr', gender: 'female' })
            });

            if (result && result.success) {
                // Başarılı
                document.getElementById('tts-input').value = ''; // Temizle
            } else {
                customAlert('TTS oluşturulamadı. Ses motoru çalışmıyor olabilir.', 'Hata');
            }
        } catch (e) {
            customAlert('TTS sırasında hata oluştu: ' + e.message, 'Hata');
        }
    }, 3000);
}

async function toggleScheduler() {
    const status = await api('/api/status');
    const isRunning = status?.scheduler?.running;

    const action = isRunning ? 'geçici olarak pasif yapmak' : 'tekrar aktif etmek';
    const message = isRunning
        ? 'Zamanlayıcıyı geçici olarak pasif yapmak istediğinize emin misiniz?\n\nTüm otomatik işlemler (ziller, anonslar, müzik) duracaktır.'
        : 'Zamanlayıcıyı tekrar aktif etmek istediğinize emin misiniz?';

    if (!confirm(message)) {
        return;
    }

    const endpoint = isRunning ? '/api/scheduler/stop' : '/api/scheduler/start';
    await api(endpoint, { method: 'POST' });

    // Durumu hemen güncelle
    await loadStatus();
}


// ===== SCHEDULE =====

async function loadSchedule() {
    schedule = await api('/api/schedule') || [];

    // Bugünün gününü seç (Pazartesi=0, Salı=1, ... Pazar=6)
    // JavaScript: Pazar=0, Pazartesi=1, ...
    const jsDay = new Date().getDay();
    // Dönüştür: Pazar(0)->6, Pazartesi(1)->0, ...
    selectedDay = jsDay === 0 ? 6 : jsDay - 1;

    renderDayTabs();
    renderDayControls();
    renderActivities();
}

function renderDayTabs() {
    const days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'];
    const container = document.getElementById('day-tabs');
    if (!container) return;

    container.innerHTML = schedule.map((d, i) => `
        <button class="day-tab ${i === selectedDay ? 'active' : ''} ${d.enabled ? '' : 'disabled'}" onclick="selectDay(${i})">
            <span class="day-tab-name">${days[i]}</span>
            <span class="day-tab-status">${d.enabled ? '✓' : '✗'}</span>
        </button>
    `).join('');
}

function selectDay(i) {
    selectedDay = i;
    renderDayTabs();
    renderDayControls();
    renderActivities();
}

function renderDayControls() {
    const day = schedule[selectedDay];
    const checkbox = document.getElementById('day-enabled');
    if (checkbox && day) checkbox.checked = day.enabled;
}

async function toggleDayEnabled() {
    const day = schedule[selectedDay];
    if (!day) return;
    day.enabled = document.getElementById('day-enabled').checked;
    await api('/api/schedule', { method: 'POST', body: JSON.stringify({ schedule }) });
    renderDayTabs();
}

function renderActivities() {
    const day = schedule[selectedDay];
    const container = document.getElementById('activities-list');
    if (!container || !day) return;

    const acts = day.activities || [];

    // Aktiviteleri başlangıç saatine göre sırala
    const sortedActs = [...acts].sort((a, b) => {
        return a.startTime.localeCompare(b.startTime);
    });

    container.innerHTML = sortedActs.length ? sortedActs.map(a => {
        const safeId = a.id.replace(/'/g, "\\'");

        // Kompakt detaylar - tek satırda
        let details = [];

        if (a.startSoundId) details.push(`🔔 Başlangıç: ${a.startSoundId}`);
        if (a.endSoundId) details.push(`🔔 Bitiş: ${a.endSoundId}`);
        if (a.playMusic) details.push('🎵 Mola Müziği Aktif');

        const announcementCount = (a.announcements || []).length;
        if (announcementCount > 0) {
            const times = a.announcements.map(ann => ann.time).join(', ');
            details.push(`📢 ${announcementCount} Duyuru: ${times}`);
        }

        const detailsText = details.length > 0 ? ` • ${details.join(' • ')}` : '';

        let announcementTimes = '';
        if (announcementCount > 0) {
            announcementTimes = (a.announcements || []).map(ann => ann.time).join(', ');
        }

        return `
        <div class="activity-item">
            <div class="activity-name">${a.name}</div>
            <div class="activity-time">${a.startTime} - ${a.endTime}</div>
            <div class="activity-details">
                ${a.startSoundId ? `<div class="detail-row">🔔 Başlangıç: ${a.startSoundId}</div>` : ''}
                ${a.endSoundId ? `<div class="detail-row">🔔 Bitiş: ${a.endSoundId}</div>` : ''}
                ${a.playMusic ? `<div class="detail-row">🎵 Mola Müziği Aktif</div>` : ''}
                ${announcementCount > 0 ? `<div class="detail-row">📢 ${announcementCount} Duyuru: ${announcementTimes}</div>` : ''}
            </div>
            <div class="activity-actions">
                <button type="button" class="btn-square-control" onclick="editActivity('${safeId}')" title="Düzenle">✏️</button>
                <button type="button" class="btn-square-control delete-btn" onclick="deleteActivity('${safeId}')" title="Sil">🗑️</button>
            </div>
        </div>
    `}).join('') : '<p style="color:var(--text-secondary);padding:1rem">Bu gün için etkinlik yok</p>';
}


function addActivity() {
    editingActivity = null;
    document.getElementById('activity-name').value = '';
    document.getElementById('activity-start').value = '';
    document.getElementById('activity-end').value = '';
    document.getElementById('activity-music').checked = false;

    // Duyurular listesini temizle
    document.getElementById('announcements-list').innerHTML = '';

    loadBellOptions().then(bells => {
        // Varsayılan melodi seçimi (melodi1.mp3)
        const defaultBell = bells.find(b => b.name.toLowerCase() === 'melodi1.mp3');
        if (defaultBell) {
            document.getElementById('activity-start-bell').value = defaultBell.name;
            document.getElementById('activity-end-bell').value = defaultBell.name;
        }
    });

    // Ardışık duyuru listelerini doldur
    loadAnnouncementOptions().then(opts => {
        const startSelect = document.getElementById('activity-start-announcement');
        const endSelect = document.getElementById('activity-end-announcement');
        if (startSelect) startSelect.innerHTML = opts;
        if (endSelect) endSelect.innerHTML = opts;
    });

    document.getElementById('activity-modal').classList.add('open');
}

async function loadBellOptions() {
    const bells = await api('/api/sounds/bells') || [];
    const opts = '<option value="">Seçilmedi</option>' + bells.map(b => `<option value="${b.name}">${b.name}</option>`).join('');
    const startEl = document.getElementById('activity-start-bell');
    const endEl = document.getElementById('activity-end-bell');

    if (startEl) startEl.innerHTML = opts;
    if (endEl) endEl.innerHTML = opts;

    return bells;
}

// Duyuru seçeneklerini yükleyen genel fonksiyon
async function loadAnnouncementOptions() {
    const announcements = await api('/api/sounds/announcements') || [];
    return '<option value="">Ardışık Duyuru Seç (2sn Sonra)</option>' +
        announcements.map(a => `<option value="${a.name}">${a.name}</option>`).join('');
}


// Duyuru slotu ekle
async function addAnnouncementSlot() {
    const announcementsContainer = document.getElementById('announcements-list');
    const announcementsOpts = await loadAnnouncementOptions();

    // Duyuru Seçin seçeneğini ekle (custom for slot)
    const slotOpts = announcementsOpts.replace('Ardışık Duyuru Seç (2sn Sonra)', 'Duyuru Seçin');


    // Calculate default time
    let defaultTime = '';
    const slots = announcementsContainer.querySelectorAll('.announcement-slot input[type="time"]');

    if (slots.length > 0) {
        // Last slot time + 15 mins
        const lastTime = slots[slots.length - 1].value;
        if (lastTime) {
            defaultTime = addMinutesToTime(lastTime, 15);
        }
    } else {
        // Activity start time + 15 mins
        const activityStart = document.getElementById('activity-start').value;
        if (activityStart) {
            defaultTime = addMinutesToTime(activityStart, 15);
        }
    }

    const slotId = `announcement-${Date.now()}-${Math.random()}`;
    const slotHTML = `
        <div class="announcement-slot" data-slot-id="${slotId}">
            <input type="time" class="input" value="${defaultTime}" placeholder="Saat">
            <select class="input">${slotOpts}</select>
            <button type="button" class="btn-square-control play-btn" onclick="playAnnouncementPreview('${slotId}')" title="Dinle">▶️</button>
            <button type="button" class="btn-square-control stop-btn" onclick="stopAnnouncementPreview()" title="Durdur">⏹️</button>
            <button type="button" class="btn-square-control delete-btn" onclick="removeAnnouncementSlot('${slotId}')" title="Sil">🗑️</button>
        </div>
    `;
    announcementsContainer.insertAdjacentHTML('beforeend', slotHTML);
}

// Helper to add minutes to HH:MM time
function addMinutesToTime(timeStr, minutesToAdd) {
    if (!timeStr) return '';
    const [hours, minutes] = timeStr.split(':').map(Number);
    const date = new Date();
    date.setHours(hours);
    date.setMinutes(minutes + minutesToAdd);

    const h = date.getHours().toString().padStart(2, '0');
    const m = date.getMinutes().toString().padStart(2, '0');
    return `${h}:${m}`;
}

// Duyuru slotu sil
function removeAnnouncementSlot(slotId) {
    const slot = document.querySelector(`[data-slot-id="${slotId}"]`);
    if (slot) slot.remove();
}

// Duyuru önizlemesi çal
async function playAnnouncementPreview(slotId) {
    const slot = document.querySelector(`[data-slot-id="${slotId}"]`);
    if (!slot) return;

    const select = slot.querySelector('select');
    const soundId = select.value;

    if (!soundId) {
        customAlert('Lütfen önce bir duyuru seçin.', 'Uyarı');
        return;
    }

    try {
        await api(`/api/announcement/play?filename=${encodeURIComponent(soundId)}`, { method: 'POST' });
    } catch (e) {
        customAlert('Duyuru çalınamadı.', 'Hata');
    }
}

// Duyuru önizlemesini durdur
async function stopAnnouncementPreview() {
    try {
        await api('/api/stop', { method: 'POST' });
    } catch (e) {
        console.error('Stop error:', e);
    }
}


function editActivity(id) {
    const day = schedule[selectedDay];
    const act = day?.activities?.find(a => a.id === id);
    if (!act) return;

    editingActivity = act;
    document.getElementById('activity-name').value = act.name;
    document.getElementById('activity-start').value = act.startTime;
    document.getElementById('activity-end').value = act.endTime;
    document.getElementById('activity-music').checked = act.playMusic;

    loadBellOptions().then(() => {
        document.getElementById('activity-start-bell').value = act.startSoundId || '';
        document.getElementById('activity-end-bell').value = act.endSoundId || '';
    });

    // Ardışık duyuruları yükle
    loadAnnouncementOptions().then(opts => {
        const startSelect = document.getElementById('activity-start-announcement');
        const endSelect = document.getElementById('activity-end-announcement');

        if (startSelect) {
            startSelect.innerHTML = opts;
            startSelect.value = act.startAnnouncementId || '';
        }
        if (endSelect) {
            endSelect.innerHTML = opts;
            endSelect.value = act.endAnnouncementId || '';
        }
    });


    // Duyuruları yükle
    const announcementsContainer = document.getElementById('announcements-list');
    announcementsContainer.innerHTML = '';

    if (act.announcements && act.announcements.length > 0) {
        // Duyuruları saate göre sırala (önce gelecek olan üstte)
        const sortedAnnouncements = [...act.announcements].sort((a, b) => {
            return a.time.localeCompare(b.time);
        });

        sortedAnnouncements.forEach(ann => {
            loadAnnouncementOptions().then(opts => {
                const slotOpts = opts.replace('Ardışık Duyuru Seç (2sn Sonra)', 'Duyuru Seçin');
                const slotId = `announcement-${Date.now()}-${Math.random()}`;
                const slotHTML = `
                    <div class="announcement-slot" data-slot-id="${slotId}">
                        <input type="time" class="input" value="${ann.time}" placeholder="Saat">
                        <select class="input">${slotOpts}</select>
                        <button type="button" class="btn-square-control play-btn" onclick="playAnnouncementPreview('${slotId}')" title="Dinle">▶️</button>
                        <button type="button" class="btn-square-control stop-btn" onclick="stopAnnouncementPreview()" title="Durdur">⏹️</button>
                        <button type="button" class="btn-square-control delete-btn" onclick="removeAnnouncementSlot('${slotId}')" title="Sil">🗑️</button>
                    </div>
                `;
                announcementsContainer.insertAdjacentHTML('beforeend', slotHTML);


                // Seçili duyuruyu ayarla
                const lastSlot = announcementsContainer.lastElementChild;
                const select = lastSlot.querySelector('select');
                if (select) select.value = ann.soundId;
            });
        });
    }

    document.getElementById('activity-modal').classList.add('open');
}

async function saveActivity() {
    // Duyuruları topla
    const announcementSlots = document.querySelectorAll('.announcement-slot');
    const announcements = [];

    announcementSlots.forEach(slot => {
        const time = slot.querySelector('input[type="time"]').value;
        const soundId = slot.querySelector('select').value;

        if (time && soundId) {
            announcements.push({ time, soundId });
        }
    });

    // Duyuruları saate göre sırala
    announcements.sort((a, b) => a.time.localeCompare(b.time));

    const act = {
        id: editingActivity?.id || `act_${Date.now()}`,
        name: document.getElementById('activity-name').value,
        startTime: document.getElementById('activity-start').value,
        endTime: document.getElementById('activity-end').value,
        startSoundId: document.getElementById('activity-start-bell').value,
        endSoundId: document.getElementById('activity-end-bell').value,
        startAnnouncementId: document.getElementById('activity-start-announcement').value,
        endAnnouncementId: document.getElementById('activity-end-announcement').value,
        playMusic: document.getElementById('activity-music').checked,
        announcements: announcements
    };

    if (!act.name || !act.startTime || !act.endTime) {
        alert('Tüm alanları doldurun');
        return;
    }

    const day = schedule[selectedDay];

    if (editingActivity) {
        const idx = day.activities.findIndex(a => a.id === editingActivity.id);
        if (idx >= 0) day.activities[idx] = act;
    } else {
        day.activities.push(act);
    }

    await api('/api/schedule', { method: 'POST', body: JSON.stringify({ schedule }) });
    closeModal('activity-modal');
    renderActivities();
}

async function deleteActivity(id) {
    const confirmed = await customConfirm('Etkinliği silmek istediğinize emin misiniz?', 'Silme Onayı');
    if (!confirmed) return;

    const day = schedule[selectedDay];
    day.activities = day.activities.filter(a => a.id !== id);
    await api('/api/schedule', { method: 'POST', body: JSON.stringify({ schedule }) });
    renderActivities();
    customAlert('Etkinlik silindi!', 'Başarılı');
}

function copyDay() {
    copiedDay = JSON.parse(JSON.stringify(schedule[selectedDay].activities));
    alert('Gün kopyalandı');
}

function pasteDay() {
    if (!copiedDay) { alert('Önce kopyalayın'); return; }
    schedule[selectedDay].activities = JSON.parse(JSON.stringify(copiedDay));
    api('/api/schedule', { method: 'POST', body: JSON.stringify({ schedule }) });
    renderActivities();
}

function closeModal(id) {
    document.getElementById(id)?.classList.remove('open');
}

// ===== MEDIA PLAYER =====

async function loadMediaFiles() {
    const files = await api('/api/media/files') || [];
    const container = document.getElementById('music-list');
    if (!container) return;

    // Alfabetik sırala
    files.sort((a, b) => a.name.localeCompare(b.name, 'tr'));

    container.innerHTML = files.map(f => `
        <div class="music-item">
            <span class="music-item-name">🎵 ${f.name}</span>
            <div class="music-item-actions">
                <button class="btn-icon" onclick="playMediaFile('${f.name}')" title="Çal">▶️</button>
                <button class="btn-icon" onclick="mediaStop()" title="Durdur">⏹️</button>
            </div>
        </div>
    `).join('') || '<p style="color:var(--text-secondary);padding:1rem">Müzik yok</p>';
}

async function loadRadioStations() {
    const config = await api('/api/config') || {};
    radioStations = config.radio?.stations || [];

    // Alfabetik sırala
    radioStations.sort((a, b) => a.name.localeCompare(b.name, 'tr'));

    const container = document.getElementById('radio-list');
    if (!container) return;

    container.innerHTML = radioStations.map((r) => {
        // İsimleri güvenli şekilde escape et
        const safeName = r.name.replace(/'/g, "\\'");
        return `
        <div class="radio-item">
            <span class="radio-item-name">📻 ${r.name}</span>
            <div class="radio-item-actions">
                <button class="btn-icon" onclick="playRadioStation('${safeName}')" title="Çal">▶️</button>
                <button class="btn-icon" onclick="mediaStop()" title="Durdur">⏹️</button>
                <button class="btn-icon" onclick="deleteRadio('${safeName}')" title="Sil">🗑️</button>
            </div>
        </div>
    `}).join('') || '<p style="color:var(--text-secondary);padding:1rem">Radyo yok</p>';
}

async function addRadio() {
    const nameInput = document.getElementById('new-radio-name');
    const urlInput = document.getElementById('new-radio-url');

    // Element kontrolü yap (Settings sayfasında olmayabiliriz veya yüklenmemiş olabilir)
    if (!nameInput || !urlInput) {
        console.warn('Radio input elements not found');
        return;
    }

    const name = nameInput.value.trim();
    const url = urlInput.value.trim();

    if (!name || !url) {
        customAlert('Lütfen istasyon adı ve URL giriniz.', 'Eksik Bilgi');
        return;
    }

    const config = await api('/api/config') || {};
    config.radio = config.radio || {};
    config.radio.stations = config.radio.stations || [];

    // Aynı isimde var mı kontrol et
    if (config.radio.stations.some(s => s.name === name)) {
        customAlert('Bu isimde bir radyo istasyonu zaten var.', 'Hata');
        return;
    }

    config.radio.stations.push({ name, url });

    await api('/api/config', { method: 'POST', body: JSON.stringify(config) });

    // Temizle ve bildir
    nameInput.value = '';
    urlInput.value = '';
    customAlert(`"${name}" istasyonu başarıyla eklendi!`, 'Başarılı');

    loadRadioStations();
}

async function deleteRadio(stationName) {
    const confirmed = await customConfirm(`"${stationName}" istasyonunu silmek istiyor musunuz?`, 'Silme Onayı');
    if (!confirmed) return;

    const config = await api('/api/config') || {};
    config.radio = config.radio || {};
    config.radio.stations = config.radio.stations || [];

    const idx = config.radio.stations.findIndex(s => s.name === stationName);

    if (idx !== -1) {
        config.radio.stations.splice(idx, 1);
        await api('/api/config', { method: 'POST', body: JSON.stringify(config) });
        loadRadioStations();
        customAlert('Radyo istasyonu silindi!', 'Başarılı');
    } else {
        customAlert('Silinecek istasyon bulunamadı.', 'Hata');
    }
}

async function playRadioStation(stationName) {
    // Çalan ses varsa otomatik durdur
    if (isAudioPlaying) {
        await api('/api/stop', { method: 'POST' });
    }

    const config = await api('/api/config') || {};
    const station = (config.radio?.stations || []).find(s => s.name === stationName);

    if (station && station.url) {
        // ÖZEL DÜZELTME: Doğrudan radyo endpointine git (dosya olarak görme)
        // playMediaFile() yerine bu çağrıyı yapıyoruz
        await api('/api/media/play/radio', {
            method: 'POST',
            body: JSON.stringify({ url: station.url })
        });

        updateNowPlaying(station.name, 'Radyo');
    } else {
        customAlert('Radyo istasyonu bulunamadı veya URL hatalı.', 'Hata');
    }
}

async function playMediaFile(filename) {
    // Çalan ses varsa otomatik durdur
    if (isAudioPlaying) {
        await api('/api/stop', { method: 'POST' });
    }
    withDebounce('music-' + filename, () =>
        api(`/api/media/play/file?filename=${encodeURIComponent(filename)}&shuffle=true`, { method: 'POST' })
        , 2000);
}

async function playRadio() {
    // Çalan ses varsa otomatik durdur
    if (isAudioPlaying) {
        await api('/api/stop', { method: 'POST' });
    }
    const url = document.getElementById('radio-url')?.value?.trim();
    if (!url) return;
    withDebounce('btn-radio', () =>
        api('/api/media/play/radio', { method: 'POST', body: JSON.stringify({ url }) })
        , 2000);
}

async function mediaToggle() {
    withDebounce('play-pause-btn', () => api('/api/media/pause', { method: 'POST' }), 500);
}

async function mediaStop() {
    withDebounce('btn-media-stop', () => api('/api/media/stop', { method: 'POST' }), 1000);
}

async function mediaNext() {
    withDebounce('btn-next', () => api('/api/media/next', { method: 'POST' }), 1000);
}

async function mediaPrev() {
    withDebounce('btn-prev', () => api('/api/media/prev', { method: 'POST' }), 1000);
}

function updateMediaVolumeLabel(val) {
    document.getElementById('media-volume-label').textContent = `${val}%`;
}

async function setMediaVolume(val) {
    await api('/api/volume', { method: 'POST', body: JSON.stringify({ channel: 'manual', volume: parseInt(val) }) });
}

// ===== SOUNDS =====

async function loadAllSounds() {
    // 3 kategori için ayrı ayrı yükle
    await Promise.all([
        loadSoundsFor('bells'),
        loadSoundsFor('announcements'),
        loadSoundsFor('music')
    ]);
}

async function loadSoundsFor(cat) {
    const sounds = await api(`/api/sounds/${cat}`) || [];
    const container = document.getElementById(`sounds-${cat}`);
    if (!container) return;

    container.innerHTML = sounds.length ? sounds.map(s => {
        const safeName = s.name.replace(/'/g, "\\'");
        return `
        <div class="sound-item">
            <span>🔊 ${s.name}</span>
            <div class="sound-actions">
                <button onclick="previewSound('${cat}', '${safeName}')" title="Çal">▶️</button>
                <button onclick="stopAll()" title="Durdur">⏹️</button>
                <button onclick="deleteSound('${cat}', '${safeName}')" title="Sil">🗑️</button>
            </div>
        </div>
    `}).join('') : '<p style="padding:0.5rem;color:var(--text-secondary);font-size:0.8rem">Dosya yok</p>';
}


async function loadSounds(cat) {
    await loadSoundsFor(cat);
}

let currentAudio = null;

async function previewSound(cat, name) {
    // Önce mevcut sesi durdur
    stopPreview();
    stopAll();

    try {
        const url = `/api/sounds/${cat}/${encodeURIComponent(name)}/preview`;
        currentPreviewAudio = new Audio(url);
        currentPreviewAudio.play().catch(e => {
            console.error('Preview error:', e);
            customAlert('Önizleme başlatılamadı: ' + e.message, 'Hata');
        });

        currentPreviewAudio.onended = () => {
            currentPreviewAudio = null;
        };
    } catch (e) {
        customAlert('Ses çalınamadı: ' + e.message, 'Hata');
    }
}

function stopAll() {
    // Tüm sesleri durdur
    api('/api/stop', { method: 'POST' }).catch(() => { });

    // Browser audio varsa durdur
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }

    // Preview varsa durdur
    stopPreview();
}

async function deleteSound(cat, name) {
    const confirmed = await customConfirm(`"${name}" dosyasını silmek istediğinizden emin misiniz?`, 'Dosya Sil');
    if (!confirmed) return;

    await api(`/api/sounds/${cat}/${encodeURIComponent(name)}`, { method: 'DELETE' });
    loadSoundsFor(cat);
}

async function uploadFiles(files) {
    const fd = new FormData();
    for (const f of files) fd.append('files', f);
    await fetch(`/api/sounds/${currentCategory}/upload`, { method: 'POST', body: fd });
    loadSounds(currentCategory);
}

// ===== SPECIAL DAYS =====

async function loadSpecialDays() {
    // Holidays
    const holidays = await api('/api/holidays') || {};
    document.getElementById('holiday-country').value = holidays.country || 'TR';

    // Yılın tüm tatillerini göster
    const allHolidays = holidays.all_holidays || holidays.upcoming_holidays || [];
    const holList = document.getElementById('holidays-list');
    if (holList) {
        holList.innerHTML = allHolidays.map(h => `
            <div class="holiday-item">
                <div class="holiday-info">
                    <span class="holiday-date">${h.date}</span>
                    <span class="holiday-name">${h.name}</span>
                    <span class="holiday-status ${h.muted ? 'muted' : 'active'}">${h.muted ? '🔇 Sessiz' : '🔔 Aktif'}</span>
                </div>
                <label class="holiday-toggle">
                    <input type="checkbox" ${h.muted ? '' : 'checked'} 
                           onchange="toggleHolidayMute('${h.date}', !this.checked)">
                    <span class="toggle-slider"></span>
                </label>
            </div>
        `).join('') || '<p style="padding:1rem;color:var(--text-secondary)">Tatil yok</p>';
    }

    // Birthdays
    await loadBirthdays();
}


async function loadBirthdays() {
    const status = await api('/api/birthdays') || {};
    let people = status.people || await api('/api/birthdays/people') || [];

    // Bugünü al (DD.MM formatı)
    const today = new Date();
    const todayStr = today.getDate().toString().padStart(2, '0') + '.' +
        (today.getMonth() + 1).toString().padStart(2, '0');

    // Türkçe ay isimleri
    const monthNames = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
        'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];

    // Tarihi Türkçe formata çevir: "01 Ocak 1972"
    function formatTurkishDate(dateStr) {
        if (!dateStr) return 'Tarih yok';
        const parts = dateStr.split('.');
        if (parts.length === 3) {
            const day = parts[0];
            const month = monthNames[parseInt(parts[1]) - 1] || parts[1];
            const year = parts[2];
            return `${day} ${month} ${year}`;
        } else if (parts.length === 2) {
            const day = parts[0];
            const month = monthNames[parseInt(parts[1]) - 1] || parts[1];
            return `${day} ${month}`;
        }
        return dateStr;
    }

    // Sırala - varsayılan tarihe göre (gün-ay)
    if (birthdaySortBy === 'name') {
        people.sort((a, b) => a.name.localeCompare(b.name, 'tr'));
    } else {
        people.sort((a, b) => {
            // Bugün olanlar en üste
            const aToday = a.date?.startsWith(todayStr);
            const bToday = b.date?.startsWith(todayStr);
            if (aToday && !bToday) return -1;
            if (!aToday && bToday) return 1;

            // Tarihe göre sırala (Ay ve Gün olarak)
            const getMonthDay = (d) => {
                if (!d) return 9999;
                const p = d.split('.');
                if (p.length < 2) return 9999;
                // Ay * 100 + Gün (Örn: 01.02 -> 201, 02.01 -> 102)
                return parseInt(p[1]) * 100 + parseInt(p[0]);
            };
            return getMonthDay(a.date) - getMonthDay(b.date);
        });
    }

    const container = document.getElementById('birthday-list');
    if (!container) return;

    container.innerHTML = people.length ? people.map((p, index) => {
        const isToday = p.date?.startsWith(todayStr);
        const formattedDate = formatTurkishDate(p.date);

        return `
        <div class="birthday-item ${isToday ? 'birthday-today' : ''}" data-person-name="${p.name}" data-person-date="${p.date || ''}">
            <span class="birthday-name">🎂 ${p.name}</span>
            <span class="birthday-date">${formattedDate}</span>
            <div class="birthday-actions">
                <button class="announce-btn" title="Manuel Duyuru">📢</button>
                <button class="edit-btn" title="Düzenle">✏️</button>
                <button class="delete-btn" title="Sil">🗑️</button>
            </div>
        </div>
    `}).join('') : '<p style="color:var(--text-secondary);padding:1rem">Doğum günü yok</p>';

    // Event listeners ekle
    container.querySelectorAll('.announce-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            // Button -> birthday-actions -> birthday-item
            const item = e.currentTarget.parentElement.parentElement;
            if (!item || !item.dataset.personName) {
                console.error('Birthday item not found');
                return;
            }
            const name = item.dataset.personName;
            console.log('Announcing birthday for:', name);
            announceBirthday(name);
        });
    });

    container.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            // Button -> birthday-actions -> birthday-item
            const item = e.currentTarget.parentElement.parentElement;
            if (!item || !item.dataset.personName) {
                console.error('Birthday item not found');
                return;
            }
            const name = item.dataset.personName;
            const date = item.dataset.personDate;
            console.log('Editing birthday:', name, date);
            editBirthday(name, date);
        });
    });

    container.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            // Button -> birthday-actions -> birthday-item
            const item = e.currentTarget.parentElement.parentElement;
            if (!item || !item.dataset.personName) {
                console.error('Birthday item not found');
                return;
            }
            const name = item.dataset.personName;
            console.log('Deleting birthday:', name);
            deleteBirthday(name);
        });
    });

    // Template'i yükle
    const templateInput = document.getElementById('birthday-template');
    if (templateInput && status.template) {
        templateInput.value = status.template;
    }

    // Anons saatlerini yükle
    const times = status.announcement_times || ['09:00', '12:00'];
    const time1 = document.getElementById('announce-time-1');
    const time2 = document.getElementById('announce-time-2');
    const time3 = document.getElementById('announce-time-3');
    if (time1) time1.value = times[0] || '';
    if (time2) time2.value = times[1] || '';
    if (time3) time3.value = times[2] || '';
}

async function saveBirthdayTemplate() {
    const template = document.getElementById('birthday-template')?.value?.trim();
    if (!template) {
        customAlert('Lütfen bir mesaj girin.', 'Uyarı');
        return;
    }

    if (!template.includes('{name}')) {
        const confirmed = await customConfirm('Mesajınızda {name} etiketi yok. Kişi adı görünmeyecek. Devam etmek istiyor musunuz?', 'Uyarı');
        if (!confirmed) return;
    }

    await api('/api/birthdays/template', {
        method: 'POST',
        body: JSON.stringify({ template })
    });

    customAlert('Doğum günü mesajı kaydedildi!', 'Başarılı');
}

// Manuel doğum günü duyurusu
async function announceBirthday(name) {
    // Şablonu sunucudan al
    const status = await api('/api/birthdays');
    const template = status?.template || 'Bugün {name} isimli çalışanımızın doğum günü. Kendisine mutlu yıllar diliyoruz!';

    // Şablondaki {name} yerine gerçek ismi koy
    const text = template.replace('{name}', name);

    await api('/api/tts', {
        method: 'POST',
        body: JSON.stringify({ text, language: 'tr', gender: 'female' })
    });
}

async function loadAnnouncementTimes() {
    const status = await api('/api/birthdays') || {};
    const times = status.announcement_times || ['09:00', '12:00'];

    const time1 = document.getElementById('announce-time-1');
    const time2 = document.getElementById('announce-time-2');
    const time3 = document.getElementById('announce-time-3');
    if (time1) time1.value = times[0] || '';
    if (time2) time2.value = times[1] || '';
    if (time3) time3.value = times[2] || '';
}

async function saveAnnouncementTimes() {
    const time1 = document.getElementById('announce-time-1')?.value || '';
    const time2 = document.getElementById('announce-time-2')?.value || '';
    const time3 = document.getElementById('announce-time-3')?.value || '';

    // Boş olmayanları filtrele
    const times = [time1, time2, time3].filter(t => t !== '');

    await api('/api/birthdays/times', {
        method: 'POST',
        body: JSON.stringify({ times })
    });

    // Feedback
    const btn = document.activeElement;
    if (btn && btn.tagName === 'INPUT') {
        // Input içindeyken save oluyorsa (onchange), belki ufak bir bildirim?
        // Şimdilik gerek yok, kullanıcı değişikliği yapmış olur.
    }
}

function editBirthday(name, date) {
    console.log('editBirthday called with:', name, date);

    const nameInput = document.getElementById('person-name');
    const dateInput = document.getElementById('person-date');

    if (!nameInput || !dateInput) {
        console.error('Form inputs not found');
        return;
    }

    nameInput.value = name;

    // Tarih formatını HTML date input formatına çevir (YYYY-MM-DD)
    if (date && date.includes('.')) {
        const parts = date.split('.');
        if (parts.length >= 3) {
            // DD.MM.YYYY -> YYYY-MM-DD
            const day = parts[0].padStart(2, '0');
            const month = parts[1].padStart(2, '0');
            const year = parts[2];
            dateInput.value = `${year}-${month}-${day}`;
        } else if (parts.length === 2) {
            // DD.MM -> 2000-MM-DD (varsayılan yıl)
            const day = parts[0].padStart(2, '0');
            const month = parts[1].padStart(2, '0');
            dateInput.value = `2000-${month}-${day}`;
        }
    }

    console.log('Form populated:', nameInput.value, dateInput.value);
}

async function deleteBirthday(name) {
    const confirmed = await customConfirm(`${name} adlı kişiyi silmek istediğinize emin misiniz?`, 'Silme Onayı');
    if (!confirmed) return;

    await api(`/api/birthdays/person/${encodeURIComponent(name)}`, {
        method: 'DELETE'
    });

    loadBirthdays();
    customAlert('Kişi silindi!', 'Başarılı');
}

function sortBirthdays(by) {
    birthdaySortBy = by;
    loadBirthdays();
}

async function setHolidayCountry() {
    const country = document.getElementById('holiday-country').value;
    await api(`/api/holidays/country?country=${country}`, { method: 'POST' });
    loadSpecialDays();
}


async function toggleHolidayMute(date, muted) {
    await api(`/api/holidays/mute?date=${encodeURIComponent(date)}&muted=${muted}`, { method: 'POST' });
    // Tatilleri yeniden yükle
    loadSpecialDays();
}


async function addPerson() {
    const name = document.getElementById('person-name')?.value?.trim();
    const dateInput = document.getElementById('person-date')?.value;
    if (!name || !dateInput) { alert('İsim ve tarih gerekli'); return; }

    // YYYY-MM-DD formatını kullan
    await api('/api/birthdays/person', {
        method: 'POST',
        body: JSON.stringify({ name, date: dateInput })
    });

    document.getElementById('person-name').value = '';
    document.getElementById('person-date').value = '';
    loadBirthdays();
}

async function removePerson(name) {
    await api(`/ api / birthdays / person / ${encodeURIComponent(name)} `, { method: 'DELETE' });
    loadBirthdays();
}

function importBirthdays() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv,.xlsx';
    input.onchange = async () => {
        const fd = new FormData();
        fd.append('file', input.files[0]);
        await fetch('/api/birthdays/import', { method: 'POST', body: fd });
        loadBirthdays();
    };
    input.click();
}

// ===== SETTINGS =====

async function loadSettings() {
    const config = await api('/api/config') || {};
    const volumes = config.volumes || {};

    ['bell', 'announcement', 'music', 'manual'].forEach(ch => {
        const slider = document.getElementById(`vol-${ch}`);
        const label = document.getElementById(`vol-${ch}-label`);
        if (slider && volumes[ch] !== undefined) {
            slider.value = volumes[ch];
            if (label) label.textContent = `${volumes[ch]}%`;
        }
    });

    // Company name
    const companyInput = document.getElementById('company-name');
    if (companyInput) companyInput.value = config.company_name || '';

    document.getElementById('auto-start').checked = config.startup?.auto_start ?? true;
    document.getElementById('open-browser').checked = config.startup?.open_browser ?? true;
    document.getElementById('startup-sound').checked = config.startup?.play_startup_sound ?? true;

    // Mola müziği dropdown'ını doldur
    await loadBreakMusicOptions();
}

async function loadBreakMusicOptions() {
    const config = await api('/api/config') || {};
    const select = document.getElementById('break-music-source');
    if (!select) return;

    // Mevcut seçimi al
    const currentRadioEnabled = config.radio?.enabled ?? false;
    const currentRadioUrl = config.radio?.url || '';

    // Dropdown'ı temizle ve yerel MP3'ü ekle
    select.innerHTML = '<option value="local">🎵 Yerel MP3 Dosyaları</option>';

    // Kayıtlı radyo istasyonlarını ekle
    const stations = config.radio?.stations || [];
    stations.forEach((station, index) => {
        const option = document.createElement('option');
        option.value = `radio-${index}`;
        option.textContent = `📻 ${station.name}`;
        option.dataset.url = station.url;
        select.appendChild(option);
    });

    // Mevcut seçimi ayarla
    if (currentRadioEnabled && currentRadioUrl) {
        // URL'e göre eşleşen istasyonu bul
        const matchingStation = stations.findIndex(s => s.url === currentRadioUrl);
        if (matchingStation !== -1) {
            select.value = `radio-${matchingStation}`;
        } else {
            select.value = 'local';
        }
    } else {
        select.value = 'local';
    }
}

// ===== PREVIEW LOGIC =====
let currentPreviewAudio = null;

function previewBell(selectId) {
    const select = document.getElementById(selectId);
    if (!select || !select.value) {
        customAlert('Lütfen önce bir ses seçin.', 'Uyarı');
        return;
    }

    const filename = select.value;
    // Otomatik kategori belirleme: ID 'announcement' içeriyorsa 'announcements' klasörüne bak
    const category = selectId.includes('announcement') ? 'announcements' : 'bells';

    stopPreview(); // Varsa önceki çalmayı durdur

    // URL oluştur: /api/sounds/{category}/{filename}/preview
    const url = `/api/sounds/${category}/${filename}/preview`;

    currentPreviewAudio = new Audio(url);
    currentPreviewAudio.play().catch(e => {
        console.error('Preview error:', e);
        customAlert('Önizleme başlatılamadı: ' + e.message, 'Hata');
    });

    currentPreviewAudio.onended = () => {
        currentPreviewAudio = null;
    };
}

function stopPreview() {
    if (currentPreviewAudio) {
        currentPreviewAudio.pause();
        currentPreviewAudio.currentTime = 0;
        currentPreviewAudio = null;
    }
}

async function updateBreakMusicSource() {
    const select = document.getElementById('break-music-source');
    if (!select) return;

    const config = await api('/api/config') || {};

    if (select.value === 'local') {
        // Yerel MP3 seçildi
        config.radio = config.radio || {};
        config.radio.enabled = false;
        config.radio.url = '';
    } else if (select.value.startsWith('radio-')) {
        // Radyo istasyonu seçildi
        const index = parseInt(select.value.replace('radio-', ''));
        const stations = config.radio?.stations || [];

        if (stations[index]) {
            config.radio = config.radio || {};
            config.radio.enabled = true;
            config.radio.url = stations[index].url;
        }
    }

    await api('/api/config', { method: 'POST', body: JSON.stringify(config) });
    customAlert('Mola müziği kaynağı güncellendi!', 'Başarılı');
}


async function loadVolumes() {
    const volumes = await api('/api/volumes') || {};
    ['bell', 'announcement', 'music', 'manual'].forEach(ch => {
        const slider = document.getElementById(`vol-${ch}`);
        const label = document.getElementById(`vol-${ch}-label`);
        if (slider && volumes[ch] !== undefined) {
            slider.value = volumes[ch];
            if (label) label.textContent = `${volumes[ch]}%`;
        }
    });

    const mediaVol = document.getElementById('media-volume');
    const mediaLabel = document.getElementById('media-volume-label');
    if (mediaVol && volumes.manual !== undefined) {
        mediaVol.value = volumes.manual;
        if (mediaLabel) mediaLabel.textContent = `${volumes.manual}%`;
    }
}

function updateVolumeLabel(ch, val) {
    const label = document.getElementById(`vol-${ch}-label`);
    if (label) label.textContent = `${val}%`;
}

async function setVolume(ch, val) {
    await api('/api/volume', { method: 'POST', body: JSON.stringify({ channel: ch, volume: parseInt(val) }) });

    // Media player slider'ı da güncelle
    if (ch === 'manual') {
        const mediaVol = document.getElementById('media-volume');
        const mediaLabel = document.getElementById('media-volume-label');
        if (mediaVol) mediaVol.value = val;
        if (mediaLabel) mediaLabel.textContent = `${val}%`;
    }
}

async function saveSettings() {
    const config = await api('/api/config') || {};

    // Company name
    const companyInput = document.getElementById('company-name');
    if (companyInput) {
        config.company_name = companyInput.value.trim();
        updateCompanyDisplay(config.company_name);
    }

    config.startup = {
        auto_start: document.getElementById('auto-start')?.checked ?? true,
        open_browser: document.getElementById('open-browser')?.checked ?? true,
        play_startup_sound: document.getElementById('startup-sound')?.checked ?? true
    };

    config.radio = {
        ...config.radio,
        enabled: document.getElementById('radio-enabled')?.checked ?? false,
        url: document.getElementById('default-radio')?.value || ''
    };

    await api('/api/config', { method: 'POST', body: JSON.stringify(config) });
}

async function loadCompanyName() {
    const config = await api('/api/config') || {};
    updateCompanyDisplay(config.company_name);
}

function updateCompanyDisplay(name) {
    const el = document.getElementById('header-company');
    if (el) el.textContent = name || '';
}

// ===== BACKUP =====

function exportJSON() { window.location.href = '/api/backup/export/json'; }
function exportExcel() { window.location.href = '/api/backup/export/excel'; }

function importBackup() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json,.xlsx';
    input.onchange = async () => {
        const fd = new FormData();
        fd.append('file', input.files[0]);
        const res = await fetch('/api/backup/import', { method: 'POST', body: fd });
        if (res.ok) { alert('Yedek yüklendi'); location.reload(); }
        else alert('Hata oluştu');
    };
    input.click();
}

// ===== SYSTEM CONTROL =====

async function restartApp() {
    if (!confirm('Uygulamayı yeniden başlatmak istediğinizden emin misiniz?')) {
        return;
    }

    const btn = event.target;
    btn.innerHTML = '🔄 Yeniden başlatılıyor...';
    btn.disabled = true;

    try {
        await api('/api/system/restart', { method: 'POST' });
        btn.innerHTML = '✅ Yeniden başlatıldı';
        setTimeout(() => location.reload(), 2000);
    } catch (e) {
        customAlert('Hata: ' + e.message, 'Hata');
        btn.disabled = false;
        btn.innerHTML = 'Uygulamayı Yeniden Başlat';
    }
}

async function shutdownApp() {
    if (!confirm('Uygulamayı tamamen kapatmak istediğinizden emin misiniz?\n\nTüm işlemler sonlandırılacak ve uygulama kapanacak.')) {
        return;
    }

    const btn = event.target;
    btn.innerHTML = '🔴 Kapatılıyor...';
    btn.disabled = true;

    try {
        await api('/api/system/shutdown', { method: 'POST' });
        btn.innerHTML = '✅ Kapatıldı';
        document.body.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;gap:1rem;"><h1>🔴 Uygulama Kapatıldı</h1><p>Bu pencereyi kapatabilirsiniz.</p></div>';
    } catch (e) {
        customAlert('Hata: ' + e.message, 'Hata');
        btn.disabled = false;
        btn.innerHTML = 'Uygulamayı Tamamen Kapat';
    }
}



// ===== AUTHENTICATION =====

function handlePasswordKeypress(e) {
    if (e.key === 'Enter') {
        verifyPassword();
    }
}

async function verifyPassword() {
    const passwordInput = document.getElementById('admin-password');
    const password = passwordInput.value;

    if (!password) {
        customAlert('Lütfen şifre giriniz.', 'Hata');
        return;
    }

    try {
        const res = await api('/api/auth/verify', {
            method: 'POST',
            body: JSON.stringify({ password })
        });

        if (res && res.success) {
            // Başarılı
            document.getElementById('ads-login-form').style.display = 'none';
            document.getElementById('ads-settings-form').style.display = 'block';
            passwordInput.value = ''; // Şifreyi temizle
            loadAdSenseCode(); // Kodları yükle
        } else {
            customAlert('Hatalı şifre!', 'Hata');
            passwordInput.value = '';
            passwordInput.focus();
        }
    } catch (e) {
        customAlert('Doğrulama hatası: ' + e.message, 'Hata');
    }
}

function logoutAds() {
    document.getElementById('ads-login-form').style.display = 'block';
    document.getElementById('ads-settings-form').style.display = 'none';
    document.getElementById('adsense-code').value = ''; // Kodu temizle (güvenlik için)
}

// ===== ADSENSE =====

async function loadAdSenseCode() {
    try {
        // 1. Önce ads.txt'den Publisher ID'yi okumaya çalış
        let pubId = '';
        try {
            const response = await fetch('/ads.txt');
            if (response.ok) {
                const text = await response.text();
                // "google.com, pub-0943242990068977, ..." formatını parse et
                const match = text.match(/pub-\d+/);
                if (match) {
                    pubId = match[0];
                    console.log('Publisher ID found in ads.txt:', pubId);
                }
            }
        } catch (e) {
            console.error('Error reading ads.txt:', e);
        }

        // 2. Config'deki mevcut kodu al
        const config = await api('/api/config') || {};
        let adsenseCode = config.adsenseCode || '';

        // 3. Eğer ads.txt'den ID okunduysa
        if (pubId) {
            // Publisher ID formatı: pub-XXXXXXXXXXXXXXXX (ads.txt içinde)
            // AdSense script formatı: ca-pub-XXXXXXXXXXXXXXXX
            const clientId = `ca-${pubId}`;

            // Eğer kayıtlı kod varsa, içindeki pub id'yi güncelle
            if (adsenseCode && adsenseCode.includes('data-ad-client')) {
                adsenseCode = adsenseCode.replace(/data-ad-client="[^"]*"/g, `data-ad-client="${clientId}"`);
                adsenseCode = adsenseCode.replace(/client=[^"&]*/g, `client=${clientId}`);
            } else {
                // Kod yoksa yeni oluştur
                adsenseCode = `<!-- Generated from ads.txt (${pubId}) -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${clientId}"
     crossorigin="anonymous"></script>
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="${clientId}"
     data-ad-slot="YOUR_AD_SLOT_ID_HERE"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({});
</script>`;
            }
        }

        const textarea = document.getElementById('adsense-code');
        if (textarea) {
            textarea.value = adsenseCode;
        }

        // Reklam alanına kodu yerleştir
        renderAdSense(adsenseCode);

    } catch (error) {
        console.error('Error in loadAdSenseCode:', error);
    }
}

async function saveAdSenseCode() {
    const textarea = document.getElementById('adsense-code');
    if (!textarea) return;

    const adsenseCode = textarea.value.trim();

    const config = await api('/api/config') || {};
    config.adsenseCode = adsenseCode;

    await api('/api/config', {
        method: 'POST',
        body: JSON.stringify(config)
    });

    customAlert('Reklam kodu kaydedildi! Sayfa yenileniyor...', 'Başarılı');

    // 2 saniye sonra sayfayı yenile
    setTimeout(() => {
        location.reload();
    }, 2000);
}

function renderAdSense(code) {
    const container = document.querySelector('.adsense-content');
    if (!container) return;

    if (code && code.trim()) {
        // Demo placeholder'ı gizle ve gerçek kodu göster
        container.innerHTML = code;

        // Script tag'lerini çalıştır
        const scripts = container.querySelectorAll('script');
        scripts.forEach(oldScript => {
            const newScript = document.createElement('script');
            Array.from(oldScript.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });
            newScript.textContent = oldScript.textContent;
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });
    }
}

// ===== EXPOSE FUNCTIONS TO GLOBAL SCOPE =====
// Critical functions must be accessible from inline onclick handlers

window.showPage = showPage;
window.selectDay = selectDay;
window.addActivity = addActivity;
window.editActivity = editActivity;
window.deleteActivity = deleteActivity;
window.saveActivity = saveActivity;
window.copyDay = copyDay;
window.pasteDay = pasteDay;
window.toggleDayEnabled = toggleDayEnabled;
window.closeModal = closeModal;
window.playBell = playBell;
window.stopAll = stopAll;
window.playTTS = playTTS;
window.stopAnnouncement = stopAnnouncement;
window.toggleScheduler = toggleScheduler;
window.mediaToggle = mediaToggle;
window.mediaStop = mediaStop;
window.playMediaFile = playMediaFile;
window.playRadio = playRadio;
window.playRadioStation = playRadioStation;
window.deleteRadio = deleteRadio;
// window.showAddRadio = showAddRadio; // Removed
// window.hideAddRadio = hideAddRadio; // Removed
window.addRadio = addRadio;
window.playSound = playSound;
window.deleteSound = deleteSound;
window.addPerson = addPerson;
window.deletePerson = deletePerson;
window.sortBirthdays = sortBirthdays;
window.importBirthdays = importBirthdays;
window.saveBirthdayTemplate = saveBirthdayTemplate;
window.saveAnnouncementTimes = saveAnnouncementTimes;
window.setHolidayCountry = setHolidayCountry;
window.loadSpecialDays = loadSpecialDays;
window.loadSettings = loadSettings;
window.saveSettings = saveSettings;
window.setVolume = setVolume;
window.updateVolumeLabel = updateVolumeLabel;
window.updateMediaVolumeLabel = updateMediaVolumeLabel;
window.setMediaVolume = setMediaVolume;
window.updateBreakMusicSource = updateBreakMusicSource;
window.exportJSON = exportJSON;
window.exportExcel = exportExcel;
window.importBackup = importBackup;
window.restartApp = restartApp;
window.shutdownApp = shutdownApp;
window.verifyPassword = verifyPassword;
window.logoutAds = logoutAds;
window.saveAdSenseCode = saveAdSenseCode;
window.previewBell = previewBell;
window.stopPreview = stopPreview;
window.addAnnouncementSlot = addAnnouncementSlot;
window.removeAnnouncementSlot = removeAnnouncementSlot;
window.playAnnouncementPreview = playAnnouncementPreview;
window.stopAnnouncementPreview = stopAnnouncementPreview;

console.log('[Global] All critical functions exposed to window object');
