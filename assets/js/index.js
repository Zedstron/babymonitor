let isRecording = false;
let seconds = 0;

function timeAgo(inputTime) {
  const time = new Date(inputTime).getTime();
  const now = Date.now();
  const diff = Math.floor((now - time) / 1000);

  if (diff < 5) return "just now";
  if (diff < 60) return `${diff} sec${diff === 1 ? "" : "s"} ago`;

  const mins = Math.floor(diff / 60);
  if (mins < 60) return `${mins} min${mins === 1 ? "" : "s"} ago`;

  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;

  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function toggleDarkMode() {
    const html = document.documentElement;
    const isDark = html.classList.contains('dark');

    if (isDark) {
        html.classList.remove('dark');
        html.classList.add('light');
        localStorage.setItem('theme', 'light');
    } else {
        html.classList.remove('light');
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    }
}

function initDarkMode() {
    const html = document.documentElement;
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        html.classList.add('dark');
        html.classList.remove('light');
    } else {
        html.classList.add('light');
        html.classList.remove('dark');
    }
}

initDarkMode();

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');

    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('bg-indigo-50', 'dark:bg-indigo-900/30', 'text-primary');
        el.classList.add('text-slate-500', 'dark:text-slate-400', 'hover:bg-slate-50', 'dark:hover:bg-slate-800');
    });

    const activeNav = document.getElementById(`nav-${tabId}`);
    activeNav.classList.remove('text-slate-500', 'dark:text-slate-400', 'hover:bg-slate-50', 'dark:hover:bg-slate-800');
    activeNav.classList.add('bg-indigo-50', 'dark:bg-indigo-900/30', 'text-primary');

    document.getElementById('page-title').innerText = tabId.toUpperCase();
}

function toggleNotifications() {
    const dropdown = document.getElementById('notif-dropdown');
    const isHidden = dropdown.classList.contains('opacity-0');

    if (isHidden) {
        dropdown.classList.remove('opacity-0', 'scale-95', 'pointer-events-none');
        dropdown.classList.add('opacity-100', 'scale-100');
    } else {
        dropdown.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
        dropdown.classList.remove('opacity-100', 'scale-100');
    }
}

document.addEventListener('click', function (event) {
    const dropdown = document.getElementById('notif-dropdown');
    const button = event.target.closest('button');

    if (!dropdown.contains(event.target) && !button) {
        dropdown.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
        dropdown.classList.remove('opacity-100', 'scale-100');
    }
});

function changeResolution() {
    const resolution = document.getElementById('video-resolution').value;
}

function changeQuality() {
    const quality = document.getElementById('video-quality').value;
    const badge = document.getElementById('quality-badge');
    badge.innerHTML = `<i class="fa-solid fa-video mr-1"></i> ${quality.charAt(0).toUpperCase() + quality.slice(1)}`;
}

function changeFPS() {
    const fps = document.getElementById('video-fps').value;
    document.getElementById('fps-display').innerText = fps;
}

function toggleNightLight() {
}

function toggleWhiteNoise(btn) 
{
    const isActive = btn.getAttribute('aria-pressed') === 'true';
    const newState = !isActive;

    btn.setAttribute('aria-pressed', newState.toString());

    btn.classList.toggle('bg-blue-50', newState);
    btn.classList.toggle('dark:bg-blue-900/20', newState);
    btn.classList.toggle('border-blue-200', newState);
    btn.classList.toggle('dark:border-blue-800', newState);
    btn.classList.toggle('ring-2', newState);
    btn.classList.toggle('ring-blue-400/50', newState);
    btn.classList.toggle('border-transparent', !newState);

    const icon = btn.querySelector('i');
    if (icon) {
        icon.classList.toggle('text-blue-600', newState);
        icon.classList.toggle('text-blue-500', !newState);
        icon.classList.toggle('scale-110', newState);
    }

    const dot = btn.querySelector('.w-2.h-2');
    if (dot) {
        dot.classList.toggle('bg-emerald-500', newState);
        dot.classList.toggle('shadow-sm', newState);
        dot.classList.toggle('shadow-emerald-500/30', newState);
        dot.classList.toggle('bg-slate-300', !newState);
        dot.classList.toggle('dark:bg-slate-600', !newState);
    }

    fetch("/api/whitenoise/" + (newState ? "start" : "stop"), {
        headers: { "Content-Type": "application/json" }
    }).then(d => d.json()).then(d => {
        showToast(d.message, d.status ? "success" : "error");
    });
}

function toggleRecording() {
    isRecording = !isRecording;
    const indicator = document.getElementById('recording-indicator');

    if (isRecording) {
        indicator.classList.remove('hidden');
        fetch("/api/recording/start", { 
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ pc_id: window.pc_id })
        }).then(d => d.json()).then(d => {
            showToast(d.message, d.status ? "success" : "error");
        });
    } else {
        indicator.classList.add('hidden');
        fetch("/api/recording/stop", { 
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ pc_id: window.pc_id })
        }).then(d => d.json()).then(d => {
            showToast(d.message, d.status ? "success" : "error");
        });
    }
}

function toggleNightVision()
{
}

function toggleFullscreen() {
    const video = document.getElementById('remoteVideo');
    if (video.requestFullscreen) {
        video.requestFullscreen();
    } else if (video.webkitRequestFullscreen) {
        video.webkitRequestFullscreen();
    } else if (video.msRequestFullscreen) {
        video.msRequestFullscreen();
    }
}

function takeSnapshot() 
{
    fetch("/api/snapshots/capture", { method: "POST" }).then(response => response.json()).then(data => {
        if(!data.status)
            showToast(data.message || 'Failed to capture snapshot', 'error');
    });
}

function animateAudioBars() 
{
    const bars = document.querySelectorAll('.audio-bar');
    bars.forEach(bar => {
        const height = Math.random() * 100;
        bar.style.height = `${Math.max(20, height)}%`;

        if (height > 70) {
            bar.classList.remove('bg-slate-200', 'dark:bg-slate-700');
            bar.classList.add('bg-red-500');
        } else if (height > 40) {
            bar.classList.remove('bg-slate-200', 'dark:bg-slate-700', 'bg-red-500');
            bar.classList.add('bg-amber-500');
        } else {
            bar.classList.remove('bg-red-500', 'bg-amber-500');
            bar.classList.add('bg-slate-200', 'dark:bg-slate-700');
        }
    });
}

function updateUptime() {
    seconds++;
    const hrs = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const mins = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const secs = (seconds % 60).toString().padStart(2, '0');
    document.getElementById('uptime').innerText = `${hrs}:${mins}:${secs}`;
}

async function loadRecordings(filters = {}) 
{
    try 
    {
        const params = new URLSearchParams(filters).toString();
        const response = await fetch(`/api/recordings?${params}`);
        const data = await response.json();
        
        renderRecordingsList(data.recordings);
        updateRecordingStats(data);
        
    } catch (error) {
        console.error('Error loading recordings:', error);
        document.getElementById('recordings-empty').classList.remove('hidden');
    }
}

function renderRecordingsList(recordings) 
{
    const grid = document.getElementById('recordings-grid');
    const empty = document.getElementById('recordings-empty');
    
    if (!recordings || recordings.length === 0) {
        grid.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }
    
    empty.classList.add('hidden');
    
    grid.innerHTML = recordings.map(rec => `
        <div class="recording-item p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer dark-mode-transition" 
             data-date="${rec.date}" 
             data-filename="${rec.filename}"
             onclick="selectRecording('${rec.filename}', '${rec.url}', '${rec.duration}', '${rec.created_formatted}')">
            <div class="flex items-center gap-4">
                <div class="relative w-24 h-14 bg-slate-200 dark:bg-slate-700 rounded-lg overflow-hidden flex-shrink-0 group">
                    <img src="${rec.thumbnail}" alt="Thumbnail" class="w-full h-full object-cover" onerror="this.src='/assets/img/placeholder-thumb.jpg'">
                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <i class="fa-solid fa-play text-white text-lg"></i>
                    </div>
                    <span class="absolute bottom-1 right-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded">
                        ${rec.duration_formatted}
                    </span>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-start justify-between gap-2">
                        <div>
                            <p class="font-medium text-slate-800 dark:text-slate-100 truncate dark-mode-transition">${rec.filename}</p>
                            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 dark-mode-transition">
                                <i class="fa-regular fa-calendar mr-1"></i>${rec.created_formatted}
                            </p>
                        </div>
                        <span class="text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded dark-mode-transition">
                            ${rec.size_mb} MB
                        </span>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="event.stopPropagation(); playRecording('${rec.filename}', '${rec.url}')" 
                            class="w-9 h-9 rounded-lg bg-primary/10 text-primary hover:bg-primary hover:text-white flex items-center justify-center transition-colors"
                            title="Play">
                        <i class="fa-solid fa-play text-sm"></i>
                    </button>
                    <button onclick="event.stopPropagation(); downloadRecording('${rec.filename}')" 
                            class="w-9 h-9 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-primary hover:text-white flex items-center justify-center transition-colors dark-mode-transition"
                            title="Download">
                        <i class="fa-solid fa-download text-sm"></i>
                    </button>
                    <button onclick="event.stopPropagation(); deleteRecording('${rec.filename}')" 
                            class="w-9 h-9 rounded-lg bg-rose-100 dark:bg-rose-900/30 text-rose-500 hover:bg-rose-500 hover:text-white flex items-center justify-center transition-colors"
                            title="Delete">
                        <i class="fa-solid fa-trash text-sm"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function updateRecordingStats(data) 
{
    document.getElementById('recording-count').textContent = `${data.total || 0} items`;
    
    const totalMB = data.recordings?.reduce((sum, r) => sum + (r.size_mb || 0), 0) || 0;
    const totalGB = 32;
    const percent = Math.min(100, (totalMB / (totalGB * 1024)) * 100);
    
    document.getElementById('storage-used').textContent = `${totalMB.toFixed(1)} MB`;
    document.getElementById('storage-bar').style.width = `${percent}%`;
}

function applyRecordingFilters() {
    const year = document.getElementById('filter-year').value;
    const month = document.getElementById('filter-month').value;
    const day = document.getElementById('filter-day').value;
    
    loadRecordings({ year, month, day });
}

function quickFilter(type) {
    const now = new Date();
    let filters = {};
    
    switch(type) {
        case 'today':
            filters.year = now.getFullYear().toString();
            filters.month = String(now.getMonth() + 1).padStart(2, '0');
            filters.day = String(now.getDate()).padStart(2, '0');
            break;
        case 'week':
            filters.year = now.getFullYear().toString();
            filters.month = String(now.getMonth() + 1).padStart(2, '0');
            break;
        case 'month':
            filters.year = now.getFullYear().toString();
            filters.month = String(now.getMonth() + 1).padStart(2, '0');
            break;
    }
    
    if (filters.year) document.getElementById('filter-year').value = filters.year;
    if (filters.month) document.getElementById('filter-month').value = filters.month;
    if (filters.day) document.getElementById('filter-day').value = filters.day;
    
    loadRecordings(filters);
}

function clearFilters() {
    document.getElementById('filter-year').value = '';
    document.getElementById('filter-month').value = '';
    document.getElementById('filter-day').value = '';
    loadRecordings();
}

function selectRecording(filename, url, duration, date) {
    const player = document.getElementById('recording-player');
    const placeholder = document.getElementById('player-placeholder');
    const info = document.getElementById('player-info');

    player.src = url;
    player.load();

    placeholder.classList.add('hidden');
    info.classList.remove('hidden');

    document.getElementById('player-filename').textContent = filename;
    document.getElementById('player-duration').textContent = formatDuration(duration);
    document.getElementById('player-date').textContent = date;
    document.getElementById('player-status').textContent = 'Ready to play';
    
    document.querySelectorAll('.recording-item').forEach(el => {
        el.classList.remove('bg-primary/5', 'border-l-4', 'border-primary');
    });
    event?.currentTarget?.classList?.add('bg-primary/5', 'border-l-4', 'border-primary');
}

function playRecording(filename, url) {
    selectRecording(filename, url);
    document.getElementById('recording-player').play();
    document.getElementById('player-status').textContent = 'Playing...';
}

function downloadRecording(filename) {
    window.open(`/api/recordings/file/${filename}`, '_blank');
}

async function deleteRecording(filename) {
    if (!confirm(`Delete "${filename}"? This cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/recordings/${filename}`, {
            method: 'DELETE'
        });
        
        if (response.ok) 
        {
            const item = document.querySelector(`[data-filename="${filename}"]`);
            item?.remove();

            loadRecordings();

            showToast('Recording deleted', 'success');
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showToast('Failed to delete recording', 'error');
    }
}

let playbackSpeed = 1;
function togglePlaybackSpeed() {
    const speeds = [0.5, 1, 1.5, 2];
    const currentIndex = speeds.indexOf(playbackSpeed);
    playbackSpeed = speeds[(currentIndex + 1) % speeds.length];
    
    const player = document.getElementById('recording-player');
    player.playbackRate = playbackSpeed;
    document.getElementById('playback-speed').textContent = `${playbackSpeed}x`;
    
    showToast(`Speed: ${playbackSpeed}x`, 'info');
}

function toggleFullscreenPlayer() {
    const player = document.getElementById('recording-player');
    if (player.requestFullscreen) {
        player.requestFullscreen();
    } else if (player.webkitRequestFullscreen) {
        player.webkitRequestFullscreen();
    }
}

function formatDuration(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hrs > 0) return `${hrs}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    return `${mins}:${String(secs).padStart(2, '0')}`;
}

function showLogoutConfirm() {
    document.getElementById('logout-modal').classList.remove('hidden');
    switchTab('logout');
}

function hideLogoutConfirm() {
    document.getElementById('logout-modal').classList.add('hidden');
    switchTab('dashboard');
}

async function confirmLogout() 
{
    try 
    {
        await fetch('/logout');
        showToast('Signed out successfully', 'success');

        setTimeout(() => { window.location.href = '/'; }, 1000);
    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = '/';
    }
}

function showToast(message, type = 'info') {
    document.querySelectorAll('.toast').forEach(t => t.remove());
    
    const colors = {
        success: 'bg-emerald-500',
        error: 'bg-rose-500',
        info: 'bg-slate-700',
        warning: 'bg-amber-500'
    };
    
    const icons = {
        success: 'fa-check',
        error: 'fa-xmark',
        info: 'fa-info',
        warning: 'fa-triangle-exclamation'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast fixed bottom-4 right-4 z-50 ${colors[type]} text-white px-4 py-3 rounded-xl shadow-lg flex items-center gap-3 animate-slide-up`;
    toast.innerHTML = `
        <i class="fa-solid ${icons[type]}"></i>
        <span class="text-sm font-medium">${message}</span>
        <button onclick="this.parentElement.remove()" class="ml-2 hover:opacity-80">
            <i class="fa-solid fa-xmark text-xs"></i>
        </button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 3000);
}

async function captureSnapshot() {
    try {
        const response = await fetch('/api/snapshots/capture', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            showToast('Snapshot captured!', 'success');
            reloadGallery();
        } else {
            throw new Error(data.detail || 'Capture failed');
        }
    } catch (error) {
        console.error('Capture error:', error);
        showToast('Failed to capture snapshot', 'error');
    }
}
function openMenu() {
    const aside = document.querySelector('aside');
    const overlay = document.getElementById('mobile-overlay');
    if (!aside) return;
    aside.classList.remove('-translate-x-full');
    aside.classList.add('translate-x-0');
    if (overlay) overlay.classList.remove('hidden');
}

function closeMenu() {
    const aside = document.querySelector('aside');
    const overlay = document.getElementById('mobile-overlay');
    if (!aside) return;
    aside.classList.remove('translate-x-0');
    aside.classList.add('-translate-x-full');
    if (overlay) overlay.classList.add('hidden');
}

function toggleMenu() {
    const aside = document.querySelector('aside');

    if (!aside) return;
    const isOpen = aside.classList.contains('translate-x-0');
    if (isOpen) {
        closeMenu();
    } else {
        openMenu();
    }
}

document.addEventListener('DOMContentLoaded', async () => 
{
    window.openMenu = openMenu;
    window.closeMenu = closeMenu;
    window.toggleMenu = toggleMenu;

    startConnectionUpdates();
    initPTT();
    readMediaStatus();
    initBabyAudio();
    initSettingsControls();

    await initWebRTC();
});

