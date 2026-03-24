function openAddIRModal()
{
    document.getElementById('ir-modal').classList.remove('hidden');
    document.getElementById('ir-warning').classList.add('hidden');
    document.getElementById('ir-tag-input').value = '';
}

function closeAddIRModal()
{
    document.getElementById('ir-modal').classList.add('hidden');
}

async function beginIRLearning()
{
    const tag = document.getElementById('ir-tag-input').value.trim();
    if(!tag)
    {
        showToast('Please enter a tag name', 'error');
        return;
    }

    const warning = document.getElementById('ir-warning');
    if(warning.classList.contains('hidden'))
    {
        warning.classList.remove('hidden');
        return;
    }

    const btn = document.getElementById('ir-start-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Learning';

    try
    {
        const res = await fetch('/api/ir/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tag: tag })
        });
        const data = await res.json();
        showToast(data.message || (data.status ? 'Learned' : 'Failed'), data.status ? 'success' : 'error');
        if(data.status) {
            await loadIRDevices();
            closeAddIRModal();
        }
    }
    catch(err)
    {
        console.error('IR learn error', err);
        showToast('Failed to learn IR signal', 'error');
    }
    finally
    {
        btn.disabled = false;
        btn.innerHTML = 'OK';
        document.getElementById('ir-warning').classList.add('hidden');
    }
}

async function sendIR(id)
{
    try
    {
        const res = await fetch(`/api/ir/${id}/send`, { method: 'POST' });
        const data = await res.json();
        showToast(data.message || (data.status ? 'Sent' : 'Failed'), data.status ? 'success' : 'error');
    }
    catch(err)
    {
        console.error('IR send error', err);
        showToast('Failed to send IR signal', 'error');
    }
}

async function deleteIR(id)
{
    if(!confirm('Delete this IR device?')) return;

    try
    {
        const res = await fetch(`/api/ir/${id}`, { method: 'DELETE' });
        const data = await res.json();
        showToast(data.message || (data.status ? 'Deleted' : 'Failed'), data.status ? 'success' : 'error');
        if(data.status) await loadIRDevices();
    }
    catch(err)
    {
        console.error('IR delete error', err);
        showToast('Failed to delete IR device', 'error');
    }
}

async function loadIRDevices()
{
    try
    {
        const res = await fetch('/api/ir/');
        const devices = await res.json();

        const list = Array.isArray(devices) ? devices : (devices.get ? devices.get : devices);
        renderIRList(list);
    }
    catch(err)
    {
        console.error('Failed to load IR devices', err);
    }
}

function renderIRList(devices)
{
    const container = document.getElementById('ir-list');
    if(!container) return;
    
    if(!devices || devices.length === 0){
        container.innerHTML = `
            <div class="text-center py-16 animate-fade-in">
                <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                    <i class="fa-solid fa-broadcast-tower text-3xl text-slate-400"></i>
                </div>
                <p class="text-slate-500 dark:text-slate-400 dark-mode-transition text-lg font-medium">No IR devices registered</p>
                <p class="text-sm text-slate-400 mt-1">Add your first IR remote to get started</p>
                <button onclick="openAddIRModal()" class="mt-4 inline-flex items-center gap-2 px-6 py-2.5 rounded-xl font-medium bg-primary text-white hover:bg-indigo-600 transition-colors shadow-lg shadow-indigo-200/50 dark:shadow-indigo-900/30">
                    <i class="fa-solid fa-plus"></i>
                    <span>Add Device</span>
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = devices.map(d => `
        <div class="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-700 hover:border-primary/30 dark:hover:border-primary/30 transition-all duration-200 group animate-fade-in">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/10 to-indigo-600/10 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                    <i class="fa-solid fa-poo text-primary text-lg"></i>
                </div>
                <div>
                    <p class="font-semibold text-slate-800 dark:text-slate-100 dark-mode-transition">${escapeHtml(d.tag || d.name || 'Unknown')}</p>
                    <p class="text-xs text-slate-400 mt-0.5">
                        <i class="fa-solid fa-wave-square mr-1"></i>
                        ${d.frequency ? d.frequency + ' Hz' : 'Auto-detect'} 
                    </p>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="sendIR(${d.id})" 
                    class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-indigo-600 text-white flex items-center justify-center hover:scale-105 hover:shadow-lg hover:shadow-indigo-200 dark:hover:shadow-indigo-900/50 transition-all active:scale-95" 
                    title="Send signal">
                    <i class="fa-solid fa-paper-plane text-sm"></i>
                </button>
                <button onclick="deleteIR(${d.id})" 
                    class="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-700 text-red-500 dark:text-slate-400 hover:bg-rose-500 hover:text-white flex items-center justify-center transition-all active:scale-95" 
                    title="Delete device">
                    <i class="fa-solid fa-trash text-sm"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function escapeHtml(unsafe) 
{
    return String(unsafe)
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
