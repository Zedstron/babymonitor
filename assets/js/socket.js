const MAX_READINGS = 10;
const latencyReadings = [];
let sensorsUpdate = Date.now();
let pingHandler = null;

const socket = io();

function recordLatency(ms) {
  latencyReadings.push(ms);

  if (latencyReadings.length > MAX_READINGS)
    latencyReadings.shift();
}

socket.on('connect', () => {
    pingHandler =setInterval(() => {
        socket.emit("ping", { t: Date.now() });
        document.getElementById("occupancy-time").textContent = timeAgo(Date.now() - sensorsUpdate);
    }, 12000);

    document.getElementById("connection_state_label").textContent = "Connected";
    document.getElementById("connection_state_label").classList.replace("bg-red-500", "bg-green-500");
});

socket.on('disconnect', () => {
    clearInterval(pingHandler);
    document.getElementById("connection_state_label").textContent = "Disconnected";
    document.getElementById("connection_state_label").classList.replace("bg-green-500", "bg-red-500");
});

socket.on('snapshot_new', (data) => {
    showToast('New Snapshot Captured!', 'info');
    if (document.getElementById('gallery')?.classList.contains('active')) {
        reloadGallery();
    }
});

socket.on('pong', (data) => {
    const now = Date.now();
    const latency = now - data.t;
    recordLatency(latency);
    updateLatency(latency);
});

socket.on('sensors', (data) => {
    document.getElementById("temperature-value").textContent = `${data.temperature}°C`;
    document.getElementById("humidity-value").textContent = `${data.humidity}%`;
    document.getElementById("noise-value").textContent = `${data.noise} dB`;
    document.getElementById("occupancy-value").textContent = data.occupancy;
    document.getElementById("confidence-value").textContent = data.confidence;
    document.getElementById("confidence-progress").style.width = data.confidence;

    sensorsUpdate = Date.now();
});

socket.on("media_update", (data) => {
    updateNowPlaying(data.song, data.artist, data.isPlaying);
});