function hideConnectionLoading() {
    document.getElementById('connection-loading').classList.add('hidden');
}

function showConnectionLoading() {
    document.getElementById('connection-loading').classList.remove('hidden');
}

function updateWifiBars(signalStrength) {
    const bars = [
        document.getElementById('wifi-bar-1'),
        document.getElementById('wifi-bar-2'),
        document.getElementById('wifi-bar-3'),
        document.getElementById('wifi-bar-4'),
        document.getElementById('wifi-bar-5')
    ];
    
    const label = document.getElementById('signal-label');
    
    let activeBars = 0;
    let colorClass = '';
    let labelText = '';
    
    if (signalStrength >= 80) {
        activeBars = 5;
        colorClass = 'bg-emerald-500';
        labelText = 'Excellent';
    } else if (signalStrength >= 60) {
        activeBars = 4;
        colorClass = 'bg-green-500';
        labelText = 'Good';
    } else if (signalStrength >= 40) {
        activeBars = 3;
        colorClass = 'bg-amber-500';
        labelText = 'Fair';
    } else if (signalStrength >= 20) {
        activeBars = 2;
        colorClass = 'bg-orange-500';
        labelText = 'Weak';
    } else {
        activeBars = 1;
        colorClass = 'bg-red-500';
        labelText = 'Poor';
    }
    
    bars.forEach((bar, index) => {
        if (index < activeBars) {
            bar.className = `wifi-bar w-1 ${colorClass} rounded-t transition-all duration-300`;
        } else {
            bar.className = 'wifi-bar w-1 bg-slate-300 dark:bg-slate-600 rounded-t transition-all duration-300';
        }
    });

    label.textContent = labelText;
    label.className = `text-xs font-medium ${colorClass.replace('bg-', 'text-')} dark-mode-transition`;
}

function updateBandwidth(mbps) {
    document.getElementById('bandwidth-value').textContent = `${mbps.toFixed(1)} Mbps`;
}

function updateLatency(ms) {
    const common = "mt-1 dark-mode-transition text-2xl font-bold";
    const latencyEl = document.getElementById('latency-value');
    latencyEl.textContent = `${ms} ms`;

    if (ms < 50) {
        latencyEl.className = common + 'text-emerald-600 dark:text-emerald-400';
    } else if (ms < 100) {
        latencyEl.className = common + 'text-amber-600 dark:text-amber-400';
    } else {
        latencyEl.className = common + 'text-red-600 dark:text-red-400';
    }
}

function updateUptime(hours, minutes) {
    document.getElementById('connection-uptime').textContent = `${hours}h ${minutes}m`;
}

async function loadConnectionData() {
    showConnectionLoading();
    
    try {
        const response = await fetch('/api/connection');
        const data = await response.json();

        if (data.uptime) {
            const parts = data.uptime.split(':');
            updateUptime(parseInt(parts[0]), parseInt(parts[1]));
        }

        updateWifiBars(data.signalStrength, data.signalLabel);
        updateBandwidth(parseFloat(data.bandwidth));
        
        setTimeout(() => {
            hideConnectionLoading();
        }, 500);
        
    } catch (error) {
        console.error('Error loading connection data:', error);
        updateConnectionStatus(false);
        updateWifiBars(0);
        hideConnectionLoading();
    }
}

async function startConnectionUpdates() {
    await loadConnectionData();
    setInterval(loadConnectionData, 30000);
}