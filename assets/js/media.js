let audioState = {
    isPlaying: false,
    isRemotePlaying: false,
    currentSong: null,
    currentSongId: null,
    previewVisible: true
};

class AudioPlayer {
    constructor(audioElementId) {
        this.audio = document.getElementById(audioElementId);
        this.currentBlobUrl = null;
        
        // Setup cleanup on page unload
        window.addEventListener('beforeunload', () => this.cleanup());
    }
    
    async loadFromUrl(url) {
        try {
            // Cleanup previous blob
            this.cleanup();
            
            // Fetch audio bytes
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Failed to load: ${response.status}`);
            }
            
            // Convert to blob
            const blob = await response.blob();
            this.currentBlobUrl = URL.createObjectURL(blob);
            
            // Set source
            this.audio.src = this.currentBlobUrl;
            this.audio.load();
            
            return { success: true };
            
        } catch (error) {
            console.error('Load error:', error);
            return { success: false, error: error.message };
        }
    }
    
    async play() {
        try {
            await this.audio.play();
            return { success: true };
        } catch (error) {
            console.error('Play error:', error);
            return { success: false, error: error.message };
        }
    }
    
    async pause() {
        this.audio.pause();
        return { success: true };
    }
    
    stop() {
        this.audio.pause();
        this.audio.currentTime = 0;
        return { success: true };
    }
    
    cleanup() {
        if (this.currentBlobUrl) {
            URL.revokeObjectURL(this.currentBlobUrl);
            this.currentBlobUrl = null;
        }
    }
    
    setVolume(level) {
        this.audio.volume = level / 100;
    }
}

function hidePreview() {
    const player = document.getElementById('preview-player');
    player.pause();
    player.src = '';
    document.getElementById('local-preview-container').classList.add('hidden');
    audioState.previewVisible = false;
}

function updateNowPlaying(songName, songId, isPlaying = false) {
    const titleText = document.getElementById('now-playing-title-text');
    const status = document.getElementById('now-playing-status');
    const icon = document.getElementById('now-playing-icon');
    const playPauseBtn = document.getElementById('btn-play-pause-remote');
    const stopBtn = document.getElementById('btn-stop-remote');
    const playPauseIcon = document.getElementById('btn-play-pause-remote-icon');
    
    audioState.currentSong = songName;
    audioState.currentSongId = songId;
    audioState.isRemotePlaying = isPlaying;

    titleText.textContent = songName || 'Nothing Playing';
    if (songName && songName.length > 25) {
        titleText.classList.add('animate-marquee');
    } else {
        titleText.classList.remove('animate-marquee');
    }

    if (isPlaying) {
        status.innerHTML = '<i class="fa-solid fa-circle-play mr-1 text-emerald-400"></i>Playing';
        icon.className = 'fa-solid fa-compact-disc text-5xl text-white animate-spin-slow';
        playPauseIcon.className = 'fa-solid fa-pause text-xl';
    } else if (songName) {
        status.innerHTML = '<i class="fa-regular fa-circle-pause mr-1 text-amber-400"></i>Paused';
        icon.className = 'fa-solid fa-music text-2xl text-white/80';
        playPauseIcon.className = 'fa-solid fa-play text-xl';
    } else {
        status.innerHTML = '<i class="fa-regular fa-circle-pause mr-1"></i>Idle';
        icon.className = 'fa-solid fa-music text-5xl text-white/80';
        playPauseIcon.className = 'fa-solid fa-play text-xl';
    }

    const hasSong = songName !== null && songName !== undefined;
    playPauseBtn.disabled = !hasSong;
    stopBtn.disabled = !hasSong;
}

function readMediaStatus() {
    fetch("/api/media/status").then(res => res.json()).then(data => {
        updateNowPlaying(data.song, data.artist, data.isPlaying);
    });
}

async function previewAudio()
{
    document.getElementById('local-preview-container').classList.remove('hidden');
    audioState.previewVisible = true;

    const select = document.getElementById('lullaby-select');
    const player = new AudioPlayer('preview-player');

    await player.loadFromUrl(`/api/media/${select.value}/download`);
    await player.play();
}

function playRemote() 
{
    const select = document.getElementById('lullaby-select');
    fetch(`/api/media/${select.value}/play`).then(response => response.json()).then(data => {
        if(data.status)
            showToast(data.message, "success");
        else
            showToast(data.message || 'Failed to play media', 'error');
    });
}

function pauseRemote() 
{
    const select = document.getElementById('lullaby-select');
    fetch(`/api/media/${select.value}/pause`).then(response => response.json()).then(data => {
        if(data.status)
            showToast(data.message, "success");
        else
            showToast(data.message || 'Failed to Pause media', 'error');
    });
}

function stopRemote() 
{
    const select = document.getElementById('lullaby-select');
    fetch(`/api/media/${select.value}/stop`).then(response => response.json()).then(data => {
        if(data.status)
            showToast(data.message, "success");
        else
            showToast(data.message || 'Failed to Stop media', 'error');
    });
}

function removeRemote() 
{
    const select = document.getElementById('lullaby-select');
    fetch(`/api/media/${select.value}`, {
        method: 'DELETE'
    }).then(response => response.json()).then(data => {
        if(data.status) {
            showToast(data.message, "success");
            refreshAudioList();
        }
        else
            showToast(data.message || 'Failed to Remove media', 'error');
    });
}

function refreshAudioList(){
    fetch("/api/media").then(res=>res.json()).then(data => {
        const select = document.getElementById('lullaby-select');
        select.innerHTML = '';
        data.lullabies.forEach((item, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = item;
            select.appendChild(option);
        });
    });
}

function uploadAudio() {
    const input = document.getElementById('audio-upload');
    const file = input.files[0];

    const formData = new FormData();
    formData.append("file", file);
    formData.append("filename", file.name);

    fetch('/api/media/upload', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status) {
            showToast(data.message, "success");
            refreshAudioList();
        }
        else
            showToast(data.message || "Failed to upload audio", "error");
    });
}

async function togglePlayRemote()
{
    if (!audioState.currentSongId) return;
    
    audioState.isRemotePlaying = !audioState.isRemotePlaying;
    
    if (audioState.isRemotePlaying)
        playRemote();
    else
        pauseRemote();
    
    updateNowPlaying(audioState.currentSong, audioState.currentSongId, audioState.isRemotePlaying);
}