let healthMonitor = {
    pollingInterval: null,
    intervalMs: 15000,
    isPolling: false,
    lastUpdate: null,
    retryCount: 0,
    maxRetries: 0
};

const target = document.getElementById("health");
const observer = new MutationObserver(() => 
{
    const visible = !!(target.offsetWidth || target.offsetHeight || target.getClientRects().length);
    if (!visible)
        stopHealthPolling();
    else 
        initHealthMonitor();
});

observer.observe(target, {
  attributes: true,
  attributeFilter: ["style", "class"]
});

function initHealthMonitor() {
    fetchHealthData();
    startHealthPolling();
}

function startHealthPolling() {
    if (healthMonitor.isPolling) return;
    
    healthMonitor.isPolling = true;
    healthMonitor.pollingInterval = setInterval(fetchHealthData, healthMonitor.intervalMs);
}

function stopHealthPolling() {
    if (healthMonitor.pollingInterval) {
        clearInterval(healthMonitor.pollingInterval);
        healthMonitor.pollingInterval = null;
    }
    healthMonitor.isPolling = false;
}

async function fetchHealthData() 
{
    try 
    {
        const response = await fetch('/api/health');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            updateHealthUI(result.data);
            healthMonitor.lastUpdate = new Date();
            healthMonitor.retryCount = 0;

            updateLastUpdateTime();
        } else {
            throw new Error(result.message || 'Unknown error');
        }
        
    } 
    catch (error) 
    {
        healthMonitor.retryCount++;

        if (healthMonitor.retryCount >= healthMonitor.maxRetries) {
            showToast('Failed to Fetch Health Data', 'error');
            healthMonitor.retryCount = 0;
        }
    }
}

function updateHealthUI(data) 
{
    updateElementText('cpu-circle-percent', `${data.cpu_percent}%`);
    updateElementText('cpu-temp', `${data.cpu_temp}°C`);
    updateProgressBar('cpu-temp-bar', (data.cpu_temp / 80 * 100), 100);
    updateElementText('cpu-temp-status', getTempStatus(data.cpu_temp));
    updateCircularProgress('cpu-circle', data.cpu_percent);
    
    if (data.cpu_cores && data.cpu_cores.length > 0) {
        data.cpu_cores.forEach((core, index) => {
            updateProgressBar(`cpu-core-${index + 1}`, core, 100);
            updateElementText(`cpu-core-${index + 1}-value`, `${core}%`);
        });
    }
    
    updateElementText('ram-circle-percent', `${data.ram_percent}%`);
    updateElementText('ram-used', `${data.ram_used_gb}GB`);
    updateElementText('ram-total', `${data.ram_total_gb}GB`);
    updateElementText('ram-available', `${data.ram_available_gb}GB`);
    updateProgressBar('ram-bar', data.ram_percent, 100);
    updateCircularProgress('ram-circle', data.ram_percent);

    updateElementText('storage-percent', `${data.storage_percent}%`);
    updateElementText('storage-used', `${data.storage_used_gb}GB`);
    updateElementText('storage-total', `${data.storage_total_gb}GB`);
    updateElementText('storage-free', `${data.storage_free_gb}GB`);
    updateProgressBar('storage-bar', data.storage_percent, 100);
    updateElementText('storage-system', `${data.storage_system_gb}GB`);
    updateElementText('storage-data', `${data.storage_data_gb}GB`);

    updateElementText('network-download', `${data.network_today_download_mb} MB`);
    updateElementText('network-upload', `${data.network_today_upload_mb} MB`);
    updateElementText('network-total', `${data.network_today_total_mb} MB`);
    updateElementText('network-in-speed', `${data.network_in_speed} Mbps`);
    updateElementText('network-out-speed', `${data.network_out_speed} Mbps`);

    if (data.bandwidth_7day && data.bandwidth_7day.length > 0) {
        updateBandwidthChart(data.bandwidth_7day);
    }
    updateElementText('bandwidth-week-total', `${data.bandwidth_week_total_gb} GB`);
    updateElementText('bandwidth-avg-daily', `${data.bandwidth_avg_daily_mb} MB`);
    updateElementText('bandwidth-peak', `${data.bandwidth_peak_mb} MB`);

    updateElementText('bandwidth-month-used', `${data.bandwidth_month_used_gb} GB`);
    updateElementText('bandwidth-month-limit', `${data.bandwidth_month_limit_gb} GB`);
    updateElementText('bandwidth-month-remaining', `${data.bandwidth_month_remaining_gb} GB`);
    updateProgressBar('bandwidth-month-bar', data.bandwidth_month_percent, 100);
    updateElementText('bandwidth-month-status', getBandwidthStatus(data.bandwidth_month_percent));
    updateElementClass('bandwidth-month-status', getBandwidthStatusClass(data.bandwidth_month_percent));

    updateElementText('uptime', data.uptime_formatted);
    updateElementText('boot-date', data.boot_date);
    updateElementText('process-count', data.process_count);
    updateElementText('top-process', data.top_process);
    updateElementText('load-avg', data.load_avg);
}

function updateBandwidthChart(bandwidthData) 
{
    const maxMb = Math.max(...bandwidthData.map(d => d.mb), 1);
    
    bandwidthData.forEach((day, index) => {
        const bar = document.querySelector(`.bandwidth-bar-${index + 1}`);
        const label = document.querySelector(`.bandwidth-label-${index + 1}`);
        
        if (bar) {
            const height = Math.min((day.mb / maxMb * 100), 100);
            bar.style.height = `${height}%`;
        }
        
        if (label) {
            label.textContent = day.label;
        }
    });
}

function updateElementText(elementId, value) 
{
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function updateElementClass(elementId, value) 
{
    const element = document.getElementById(elementId);
    if (element) {
        element.className = value;
    }
}

function updateProgressBar(elementId, value, max = 100) 
{
    const element = document.getElementById(elementId);
    if (element) {
        const percentage = Math.min((value / max * 100), 100);
        element.style.width = `${percentage}%`;
    }
}

function updateCircularProgress(elementId, percentage) 
{
    const circle = document.getElementById(elementId);
    if (circle) {
        const radius = parseFloat(circle.getAttribute('r')) || 56;
        const circumference = 2 * Math.PI * radius;

        circle.style.strokeDasharray = `${circumference}`;
        
        const offset = circumference * (1 - percentage / 100);
        circle.style.strokeDashoffset = `${offset}`;
    }
}

function getTempStatus(temp) 
{
    if (temp < 50) return 'Normal';
    if (temp < 70) return 'Warm';
    return 'Hot';
}

function getBandwidthStatus(percent) 
{
    if (percent < 50) return 'Healthy usage';
    if (percent < 75) return 'Moderate usage';
    if (percent < 90) return 'High usage';
    return 'Near limit';
}

function getBandwidthStatusClass(percent) 
{
    if (percent < 50) return 'text-emerald-600 dark:text-emerald-400';
    if (percent < 75) return 'text-amber-600 dark:text-amber-400';
    if (percent < 90) return 'text-orange-600 dark:text-orange-400';
    return 'text-red-600 dark:text-red-400';
}

function updateLastUpdateTime() 
{
    const now = healthMonitor.lastUpdate;
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    const updateElement = document.getElementById('health-last-update');
    if (updateElement) {
        updateElement.textContent = `Last updated: ${timeStr}`;
    }
}

function refreshHealthData() 
{
    showToast('Refreshing Health Data ...', 'info');
    fetchHealthData();
}

function setHealthPollingInterval(milliseconds) 
{
    healthMonitor.intervalMs = milliseconds;
    
    if (healthMonitor.isPolling) {
        stopHealthPolling();
        startHealthPolling();
    }
}

window.addEventListener('beforeunload', () => 
{
    stopHealthPolling();
    observer.disconnect();
});