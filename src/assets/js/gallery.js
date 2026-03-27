let galleryState = {
    currentPage: 1,
    isLoading: false,
    hasMore: true,
    totalSnapshots: 0,
    sort: 'newest',
    allSnapshots: []
};

let lightboxIndex = 0;


async function initGallery() {
    galleryState.currentPage = 1;
    galleryState.hasMore = true;
    galleryState.allSnapshots = [];
    
    const grid = document.getElementById('gallery-grid');
    const templateItems = grid.querySelectorAll('.gallery-item');
    grid.innerHTML = '';
    templateItems.forEach(item => grid.appendChild(item));
    
    await loadGalleryPage(1);

    setupInfiniteScroll();
}

async function loadGalleryPage(page) {
    if (galleryState.isLoading || !galleryState.hasMore) return;
    
    galleryState.isLoading = true;
    document.getElementById('gallery-loading').classList.remove('hidden');
    
    try {
        const sort = document.getElementById('gallery-sort').value;
        const response = await fetch(`/api/snapshots?page=${page}&limit=20&sort=${sort}`);
        const data = await response.json();
        
        galleryState.totalSnapshots = data.total;
        galleryState.hasMore = data.has_more;
        galleryState.allSnapshots = [...galleryState.allSnapshots, ...data.snapshots];
        
        // Update total count
        document.getElementById('gallery-total').textContent = data.total;
        
        // Render new snapshots
        if (data.snapshots.length > 0) {
            renderSnapshots(data.snapshots, page === 1);
            
            // Hide empty state if we have items
            if (data.total > 0) {
                document.getElementById('gallery-empty').classList.add('hidden');
            }
        }
        
        // Show end message if no more
        if (!data.has_more) {
            document.getElementById('gallery-end').classList.remove('hidden');
        }
        
        galleryState.currentPage = page;
        
    } catch (error) {
        console.error('Error loading gallery:', error);
        showToast('Failed to load snapshots', 'error');
    } finally {
        galleryState.isLoading = false;
        document.getElementById('gallery-loading').classList.add('hidden');
    }
}

function renderSnapshots(snapshots, clear = false) {
    const grid = document.getElementById('gallery-grid');
    
    if (clear) {
        const templateItems = Array.from(grid.querySelectorAll('.gallery-item'));
        grid.innerHTML = '';
        templateItems.forEach(item => grid.appendChild(item));
    }
    
    snapshots.forEach(snap => {
        const item = document.createElement('div');
        item.className = 'gallery-item group relative aspect-[4/3] rounded-xl overflow-hidden bg-slate-200 dark:bg-slate-800 cursor-pointer shadow-sm hover:shadow-xl transition-all duration-300 dark-mode-transition';
        item.dataset.filename = snap.filename;
        item.dataset.url = snap.url;
        item.dataset.date = snap.created_formatted;
        item.onclick = () => openLightbox(snap.filename, snap.url, snap.created_formatted);
        
        item.innerHTML = `
            <img src="${snap.thumbnail_url}" 
                 alt="${snap.filename}"
                 loading="lazy"
                 class="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-500"
                 onerror="this.src='/assets/img/placeholder-thumb.jpg'">
            
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <div class="absolute bottom-0 left-0 right-0 p-3">
                    <p class="text-white text-xs font-medium truncate">${snap.filename}</p>
                    <p class="text-slate-300 text-[10px] mt-0.5">
                        <i class="fa-regular fa-clock mr-1"></i>${snap.created_formatted}
                    </p>
                </div>
                
                <div class="absolute top-2 right-2 flex gap-1">
                    <button onclick="event.stopPropagation(); downloadSnapshot('${snap.filename}')" 
                            class="w-7 h-7 rounded-lg bg-white/20 backdrop-blur text-white hover:bg-white hover:text-purple-600 flex items-center justify-center transition-colors"
                            title="Download">
                        <i class="fa-solid fa-download text-xs"></i>
                    </button>
                    <button onclick="event.stopPropagation(); deleteSnapshot('${snap.filename}')" 
                            class="w-7 h-7 rounded-lg bg-white/20 backdrop-blur text-white hover:bg-rose-500 hover:text-white flex items-center justify-center transition-colors"
                            title="Delete">
                        <i class="fa-solid fa-trash text-xs"></i>
                    </button>
                </div>
            </div>
            
            <div class="absolute top-2 left-2 w-6 h-6 rounded-full bg-purple-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <i class="fa-solid fa-check text-xs"></i>
            </div>
        `;
        
        grid.appendChild(item);
    });
}

function setupInfiniteScroll() {
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && galleryState.hasMore && !galleryState.isLoading) {
                    loadGalleryPage(galleryState.currentPage + 1);
                }
            });
        },
        {
            root: null,
            rootMargin: '200px',
            threshold: 0
        }
    );

    const loadingEl = document.getElementById('gallery-loading');
    if (loadingEl) {
        observer.observe(loadingEl);
    }
}

function reloadGallery() {
    galleryState.currentPage = 1;
    galleryState.hasMore = true;
    galleryState.allSnapshots = [];
    
    const grid = document.getElementById('gallery-grid');
    grid.innerHTML = '';
    
    document.getElementById('gallery-end').classList.add('hidden');
    document.getElementById('gallery-empty').classList.add('hidden');
    
    loadGalleryPage(1);
}

function openLightbox(filename, url, date) {
    const lightbox = document.getElementById('lightbox');
    const img = document.getElementById('lightbox-image');

    lightboxIndex = galleryState.allSnapshots.findIndex(s => s.filename === filename);
    if (lightboxIndex === -1) lightboxIndex = 0;
    
    // Set image
    img.src = url;
    img.onload = () => {
        lightbox.classList.remove('hidden');
        document.body.style.overflow = 'hidden';  // Prevent background scroll
    };
    
    // Set info
    document.getElementById('lightbox-filename').textContent = filename;
    document.getElementById('lightbox-date').textContent = date;
}

function closeLightbox(event) {
    if (event && event.target !== event.currentTarget) return;
    
    const lightbox = document.getElementById('lightbox');
    lightbox.classList.add('hidden');
    document.body.style.overflow = '';
    
    // Clear image to stop loading
    document.getElementById('lightbox-image').src = '';
}

function navigateLightbox(direction) {
    const newIndex = lightboxIndex + direction;
    
    if (newIndex < 0 || newIndex >= galleryState.allSnapshots.length) {
        // Loop around
        lightboxIndex = direction > 0 ? 0 : galleryState.allSnapshots.length - 1;
    } else {
        lightboxIndex = newIndex;
    }
    
    const snap = galleryState.allSnapshots[lightboxIndex];
    if (snap) {
        openLightbox(snap.filename, snap.url, snap.created_formatted);
    }
}

function downloadCurrentLightbox() {
    const snap = galleryState.allSnapshots[lightboxIndex];
    if (snap) {
        downloadSnapshot(snap.filename);
    }
}

function deleteCurrentLightbox() {
    const snap = galleryState.allSnapshots[lightboxIndex];
    if (snap && confirm(`Delete "${snap.filename}"?`)) {
        deleteSnapshot(snap.filename).then(() => {
            // Navigate to next or close
            if (lightboxIndex >= galleryState.allSnapshots.length) {
                closeLightbox();
            } else {
                navigateLightbox(0);  // Refresh current
            }
        });
    }
}

function toggleLightboxInfo() {
    const info = document.querySelector('#lightbox .absolute.bottom-0');
    info.classList.toggle('hidden');
}

function downloadSnapshot(filename) {
    window.open(`/api/snapshots/${filename}`, '_blank');
}

async function deleteSnapshot(filename) {
    if (!confirm(`Delete "${filename}"? This cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/snapshots/${filename}`, {
            method: 'DELETE'
        });
        
        if (response.ok) 
        {
            const item = document.querySelector(`[data-filename="${filename}"]`);
            item?.remove();

            galleryState.allSnapshots = galleryState.allSnapshots.filter(s => s.filename !== filename);
            
            showToast('Snapshot deleted', 'success');
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showToast('Failed to delete snapshot', 'error');
    }
}

document.addEventListener('keydown', (e) => {
    const lightbox = document.getElementById('lightbox');
    if (!lightbox.classList.contains('hidden')) {
        if (e.key === 'Escape') closeLightbox();
        if (e.key === 'ArrowLeft') navigateLightbox(-1);
        if (e.key === 'ArrowRight') navigateLightbox(1);
    }
});