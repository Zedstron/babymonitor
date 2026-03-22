function initSettingsControls()
{
    const tabs = document.querySelectorAll(".tab-btn");

    tabs.forEach(btn => {
        btn.addEventListener("click", () => switchSettingsTab(btn.dataset.tab));
    });

    const toggle = document.getElementById('wg-service-toggle');
    if(toggle) updateWgStatusLabel(toggle.checked);

    switchSettingsTab('general');
}

function toggleWireGuardService(isOn)
{
    updateWgStatusLabel(isOn);
    fetch('/api/wireguard/' + (isOn ? "start" : "stop"), {
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(response => {
        showToast(response.message, response.status ? "success" : "error");
    })
    .catch(() => {
        showToast("Request failed", "error");
    });
}

function updateWgStatusLabel(isOn) 
{
    const label = document.getElementById('wg-status-label');
    if(label) label.textContent = isOn ? 'ON' : 'OFF';
}

function switchSettingsTab(targetTab) 
{
    const tabs = document.querySelectorAll(".tab-btn");
    const panes = document.querySelectorAll(".tab-pane");

    tabs.forEach(b => {
        b.classList.remove("text-primary", "border-primary");
        b.classList.add("text-slate-500", "dark:text-slate-400", "border-transparent");
    });

    panes.forEach(p => p.classList.add("hidden"));
    const activeBtn = document.querySelector(`.tab-btn[data-tab="${targetTab}"]`);
    const activePane = document.querySelector(`.tab-pane[data-content="${targetTab}"]`);

    if (activeBtn && activePane) {
        activeBtn.classList.remove("text-slate-500", "dark:text-slate-400", "border-transparent");
        activeBtn.classList.add("text-primary", "border-primary");
        activePane.classList.remove("hidden");
    }
}

function downloadPublicKey(text) 
{
    const blob = new Blob([text], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = 'publickey.txt';

    document.body.appendChild(a);
    a.click();

    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function updatePassword()
{
    const current_password = document.getElementById("current_password").value;
    const new_password = document.getElementById("new_password").value;
    const confirm_password = document.getElementById("confirm_password").value;

    if(current_password === "" || new_password === "" || confirm_password === "")
        return;

    if (new_password === confirm_password)
    {
        fetch('/api/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ current_password, new_password })
        })
        .then(res => res.json())
        .then(response => {
            showToast(response.message, response.status ? "success" : "error");
        })
        .catch(() => {
            showToast("Request failed", "error");
        });
    }
}

function saveProfile()
{
    const email = document.getElementById("profile_email").value;
    if (email !== "")
    {
        fetch('/api/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        })
        .then(res => res.json())
        .then(response => {
            showToast(response.message, response.status ? "success" : "error");
        })
        .catch(() => {
            showToast("Request failed", "error");
        });
    }
}

function saveWanSettings() 
{
    const inputs = document.getElementById("wanconfig").querySelectorAll('input[type="text"][id]');
    const data = {};

    inputs.forEach(input => {
        const value = input.value.trim();
        if (value !== '') {
            data[input.id] = value;
        }
    });

    fetch('/api/wireguard', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(response => {
        showToast(response.message, response.status ? "success" : "error");
    })
    .catch(() => {
        showToast("Request failed", "error");
    });
}

function saveGeneralSettings() 
{
    const name = document.getElementById('set-name').value;
    const hostname = document.getElementById('set-hostname').value;
    const latitude = document.getElementById('latitude').value;
    const longitude = document.getElementById('longitude').value;
    const cry = document.getElementById('set-cry').checked;
    const led = document.getElementById('set-led').checked;
    const buzzer = document.getElementById('set-buzzer').checked;

    fetch('/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            baby_name: name,
            cry_detection: cry,
            led_indicator: led,
            buzzer_enabled: buzzer,
            hostname: hostname,
            latitude: latitude,
            longitude: longitude
        })
    }).then(response => response.json()).then(data => {
        if(data.status)
            showToast('Settings saved successfully!', 'success');
        else
            showToast(data.message || 'Failed to save settings', 'error');
    });
}