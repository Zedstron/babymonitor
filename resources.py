from datetime import datetime
import psutil

def get_system_health():
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_cores = psutil.cpu_percent(percpu=True)
    cpu_temp = 0
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            cpu_temp = round(int(f.read()) / 1000, 1)
    except:
        cpu_temp = 45.0
    
    # RAM
    ram = psutil.virtual_memory()
    ram_total_gb = round(ram.total / (1024**3), 1)
    ram_used_gb = round(ram.used / (1024**3), 1)
    ram_available_gb = round(ram.available / (1024**3), 1)
    ram_percent = ram.percent
    
    # Storage
    storage = psutil.disk_usage('/')
    storage_total_gb = round(storage.total / (1024**3), 1)
    storage_used_gb = round(storage.used / (1024**3), 1)
    storage_free_gb = round(storage.free / (1024**3), 1)
    storage_percent = storage.percent
    
    # Network (mock - replace with actual interface stats)
    network_today_download_mb = 245.5
    network_today_upload_mb = 89.3
    network_today_total_mb = network_today_download_mb + network_today_upload_mb
    network_in_speed = 1.2
    network_out_speed = 0.8
    
    # Bandwidth 7-day trend (mock data)
    bandwidth_7day = [
        {"label": "Mon", "mb": 180},
        {"label": "Tue", "mb": 220},
        {"label": "Wed", "mb": 195},
        {"label": "Thu", "mb": 310},
        {"label": "Fri", "mb": 275},
        {"label": "Sat", "mb": 340},
        {"label": "Sun", "mb": network_today_total_mb}
    ]
    bandwidth_7day_max_mb = max(d["mb"] for d in bandwidth_7day) if bandwidth_7day else 1

    bandwidth_week_total_gb = round(sum(d["mb"] for d in bandwidth_7day) / 1024, 2)
    bandwidth_avg_daily_mb = round(sum(d["mb"] for d in bandwidth_7day) / 7, 1)
    bandwidth_peak_mb = max(d["mb"] for d in bandwidth_7day)
    
    # Monthly bandwidth
    bandwidth_month_used_gb = 12.5
    bandwidth_month_limit_gb = 100
    bandwidth_month_percent = round((bandwidth_month_used_gb / bandwidth_month_limit_gb) * 100, 1)
    bandwidth_month_remaining_gb = round(bandwidth_month_limit_gb - bandwidth_month_used_gb, 1)
    
    # Uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    uptime_days = uptime.days
    uptime_hours = uptime.seconds // 3600
    uptime_minutes = (uptime.seconds % 3600) // 60
    uptime_formatted = f"{uptime_days}d {uptime_hours}h {uptime_minutes}m"
    
    # Processes
    process_count = len(psutil.pids())
    top_process = "python3"  # Or get actual top process
    
    # Load Average
    load_avg = psutil.getloadavg()
    load_avg_str = f"{load_avg[0]:.2f} / {load_avg[1]:.2f} / {load_avg[2]:.2f}"
    
    return {
        "cpu_percent": cpu_percent,
        "cpu_cores": cpu_cores,
        "cpu_temp": cpu_temp,
        "ram_total_gb": ram_total_gb,
        "ram_used_gb": ram_used_gb,
        "ram_available_gb": ram_available_gb,
        "ram_percent": ram_percent,
        "storage_total_gb": storage_total_gb,
        "storage_used_gb": storage_used_gb,
        "storage_free_gb": storage_free_gb,
        "storage_percent": storage_percent,
        "storage_system_gb": round(storage_used_gb * 0.4, 1),
        "storage_data_gb": round(storage_used_gb * 0.6, 1),
        "network_today_download_mb": network_today_download_mb,
        "network_today_upload_mb": network_today_upload_mb,
        "network_today_total_mb": network_today_total_mb,
        "network_in_speed": network_in_speed,
        "network_out_speed": network_out_speed,
        "bandwidth_7day": bandwidth_7day,
        "bandwidth_7day_max_mb": bandwidth_7day_max_mb,
        "bandwidth_week_total_gb": bandwidth_week_total_gb,
        "bandwidth_avg_daily_mb": bandwidth_avg_daily_mb,
        "bandwidth_peak_mb": bandwidth_peak_mb,
        "bandwidth_month_used_gb": bandwidth_month_used_gb,
        "bandwidth_month_limit_gb": bandwidth_month_limit_gb,
        "bandwidth_month_percent": bandwidth_month_percent,
        "bandwidth_month_remaining_gb": bandwidth_month_remaining_gb,
        "current_month": datetime.now().strftime("%B"),
        "current_year": datetime.now().year,
        "uptime_formatted": uptime_formatted,
        "boot_date": boot_time.strftime("%b %d, %Y"),
        "process_count": process_count,
        "top_process": top_process,
        "load_avg": load_avg_str
    }