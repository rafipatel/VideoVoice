/* ═══════════════════════════════════════════════════════
   app.js — VideoVoice Frontend Application
   ═══════════════════════════════════════════════════════ */

// ── Configuration ───────────────────────────────────────
const API_BASE = window.location.origin;

// ── DOM Cache ───────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

// ── Scroll-triggered Reveal Animations ──────────────────
const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const siblings = [...entry.target.parentElement.querySelectorAll('.reveal:not(.visible)')];
        const delay = siblings.indexOf(entry.target) * 80;
        setTimeout(() => entry.target.classList.add('visible'), Math.max(delay, 0));
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.1 }
);
$$('.reveal').forEach((el) => revealObserver.observe(el));

// ── Nav scroll effect ───────────────────────────────────
const nav = $('#navbar');
let lastScroll = 0;
window.addEventListener('scroll', () => {
  const scrollY = window.scrollY;
  if (scrollY > 50) {
    nav.classList.add('scrolled');
  } else {
    nav.classList.remove('scrolled');
  }
  lastScroll = scrollY;
}, { passive: true });

// ── Mobile menu ─────────────────────────────────────────
const mobileBtn = $('#mobile-menu-btn');
const mobileNav = $('#mobile-nav');
if (mobileBtn) {
  mobileBtn.addEventListener('click', () => {
    mobileBtn.classList.toggle('active');
    mobileNav.classList.toggle('open');
  });
  // Close on link click
  $$('#mobile-nav a').forEach(a => {
    a.addEventListener('click', () => {
      mobileBtn.classList.remove('active');
      mobileNav.classList.remove('open');
    });
  });
}

// ── Active nav highlight ────────────────────────────────
const sections = $$('section[id]');
const navLinks = $$('.nav-links a:not(.btn)');
const navObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        navLinks.forEach((link) => {
          const isActive = link.getAttribute('href') === `#${entry.target.id}`;
          link.style.color = isActive ? 'var(--accent)' : '';
        });
      }
    });
  },
  { threshold: 0.3 }
);
sections.forEach((s) => navObserver.observe(s));

// ════════════════════════════════════════════════════════
// DEMO VIDEOS WALL (outputs/ + data)
// ════════════════════════════════════════════════════════
const demoVideosWall = $('#demo-videos-wall');
const demoVideosLoading = $('#demo-videos-loading');
const demoVideosError = $('#demo-videos-error');
const demoVideosEmpty = $('#demo-videos-empty');
const demoVideosLanes = $('#demo-videos-lanes');

if (demoVideosWall && demoVideosLanes) {
  loadDemoVideos();
}

async function loadDemoVideos() {
  setDemoState('loading');

  try {
    const res = await fetch(`${API_BASE}/api/demo-videos`);
    if (!res.ok) throw new Error('Failed to load demo videos');

    const payload = await res.json();
    const videos = Array.isArray(payload?.videos) ? payload.videos : [];

    if (videos.length === 0) {
      setDemoState('empty');
      return;
    }

    renderDemoVideos(videos);
    setDemoState('ready');
    setupDemoPlaybackSync(demoVideosLanes);
    setupDemoParallax(demoVideosWall, demoVideosLanes);
  } catch (err) {
    console.error(err);
    setDemoState('error');
  }
}

function setDemoState(state) {
  if (!demoVideosLanes) return;
  [demoVideosLoading, demoVideosError, demoVideosEmpty].forEach((el) => {
    if (el) el.hidden = true;
  });
  demoVideosLanes.hidden = state !== 'ready';

  if (state === 'loading' && demoVideosLoading) demoVideosLoading.hidden = false;
  if (state === 'error' && demoVideosError) demoVideosError.hidden = false;
  if (state === 'empty' && demoVideosEmpty) demoVideosEmpty.hidden = false;
}

function renderDemoVideos(videos) {
  const lanes = [...demoVideosLanes.querySelectorAll('.demos-lane')];
  if (lanes.length === 0) return;

  lanes.forEach((lane) => (lane.innerHTML = ''));
  demoVideosWall.classList.remove('parallax-enabled');

  videos.forEach((video, idx) => {
    const lane = lanes[idx % lanes.length];
    lane.appendChild(createDemoCard(video));
  });
}

function createDemoCard(videoData) {
  const card = document.createElement('article');
  card.className = 'demo-card';

  const frame = document.createElement('div');
  frame.className = 'demo-video-frame';

  const video = document.createElement('video');
  video.className = 'demo-video';
  video.controls = true;
  video.playsInline = true;
  video.preload = 'metadata';
  video.src = videoData.url;
  video.setAttribute('playsinline', '');

  const badge = document.createElement('div');
  badge.className = 'demo-badge';
  badge.textContent = (videoData.folder || 'demo').toUpperCase();

  const info = document.createElement('div');
  info.className = 'demo-info';

  const title = document.createElement('h4');
  title.textContent = formatDemoTitle(videoData.name || 'Video');

  const meta = document.createElement('p');
  meta.className = 'demo-meta';
  meta.textContent = `${videoData.folder || 'demo'} • ${formatBytes(videoData.size_bytes)} • ${formatDemoDate(videoData.modified_at)}`;

  frame.appendChild(video);
  frame.appendChild(badge);
  info.appendChild(title);
  info.appendChild(meta);
  card.appendChild(frame);
  card.appendChild(info);
  return card;
}

function formatDemoTitle(fileName) {
  const withoutExt = String(fileName).replace(/\.[^/.]+$/, '');
  const normalized = withoutExt.replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim();
  return normalized || String(fileName);
}

function formatBytes(bytes) {
  const size = Number(bytes);
  if (!Number.isFinite(size) || size <= 0) return 'Unknown size';
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = size;
  let unitIdx = 0;
  while (value >= 1024 && unitIdx < units.length - 1) {
    value /= 1024;
    unitIdx += 1;
  }
  return `${value.toFixed(unitIdx === 0 ? 0 : 1)} ${units[unitIdx]}`;
}

function formatDemoDate(modifiedAt) {
  const raw = Number(modifiedAt);
  if (!Number.isFinite(raw) || raw <= 0) return 'Unknown date';
  const ms = raw > 1e12 ? raw : raw * 1000;
  const date = new Date(ms);
  if (Number.isNaN(date.getTime())) return 'Unknown date';
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function setupDemoPlaybackSync(container) {
  if (!container || container.dataset.playbackSync === 'ready') return;
  container.dataset.playbackSync = 'ready';

  container.addEventListener(
    'play',
    (event) => {
      const currentVideo = event.target;
      if (!(currentVideo instanceof HTMLVideoElement) || !currentVideo.classList.contains('demo-video')) {
        return;
      }
      container.querySelectorAll('.demo-video').forEach((video) => {
        if (video !== currentVideo) video.pause();
      });
    },
    true
  );
}

function setupDemoParallax(wall, lanesContainer) {
  const lanes = [...lanesContainer.querySelectorAll('.demos-lane')];
  if (!wall || lanes.length === 0 || wall.dataset.parallaxReady === 'ready') return;
  wall.dataset.parallaxReady = 'ready';

  const mobileQuery = window.matchMedia('(max-width: 900px)');
  const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  const laneOffsets = [70, -100, 80];

  let enabled = false;
  let rafId = null;

  const reset = () => {
    lanes.forEach((lane) => {
      lane.style.transform = 'translate3d(0, 0, 0)';
    });
  };

  const applyParallax = () => {
    rafId = null;
    if (!enabled) return;

    const rect = wall.getBoundingClientRect();
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
    const progress = (viewportHeight - rect.top) / (viewportHeight + rect.height);
    const centered = Math.max(-1, Math.min(1, (progress - 0.5) * 2));

    lanes.forEach((lane, idx) => {
      const offset = centered * laneOffsets[idx % laneOffsets.length];
      lane.style.transform = `translate3d(0, ${offset.toFixed(1)}px, 0)`;
    });
  };

  const schedule = () => {
    if (!enabled || rafId !== null) return;
    rafId = requestAnimationFrame(applyParallax);
  };

  const evaluate = () => {
    enabled = !mobileQuery.matches && !reducedMotionQuery.matches;
    wall.classList.toggle('parallax-enabled', enabled);

    if (!enabled) {
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      reset();
      return;
    }
    schedule();
  };

  const bindMediaChange = (query, handler) => {
    if (typeof query.addEventListener === 'function') {
      query.addEventListener('change', handler);
    } else if (typeof query.addListener === 'function') {
      query.addListener(handler);
    }
  };

  bindMediaChange(mobileQuery, evaluate);
  bindMediaChange(reducedMotionQuery, evaluate);
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule, { passive: true });
  evaluate();
}

// ════════════════════════════════════════════════════════
// TAB SWITCHING (URL / Upload)
// ════════════════════════════════════════════════════════
const tabBtns = $$('.tab-btn');
const tabContents = $$('.tab-content');

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.tab;
    tabBtns.forEach(b => b.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    $(`#content-${target}`).classList.add('active');
  });
});

// ════════════════════════════════════════════════════════
// DRAG & DROP FILE UPLOAD
// ════════════════════════════════════════════════════════
const dropZone = $('#drop-zone');
const fileInput = $('#file-input');
const filePreview = $('#file-preview');
const fileName = $('#file-name');
const fileRemove = $('#file-remove');
let selectedFile = null;

if (dropZone) {
  // Click to browse
  dropZone.addEventListener('click', (e) => {
    if (e.target === fileRemove || fileRemove.contains(e.target)) return;
    if (!selectedFile) fileInput.click();
  });

  // Drag events
  ['dragenter', 'dragover'].forEach(evt => {
    dropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });
  });
  ['dragleave', 'drop'].forEach(evt => {
    dropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) handleFileSelect(fileInput.files[0]);
  });

  fileRemove.addEventListener('click', (e) => {
    e.stopPropagation();
    clearFile();
  });
}

function handleFileSelect(file) {
  // Validate type
  const validTypes = ['video/mp4', 'video/quicktime', 'video/webm'];
  if (!validTypes.includes(file.type)) {
    showToast('Please upload an MP4, MOV, or WebM file.', 'error');
    return;
  }
  // Validate size (50MB)
  if (file.size > 50 * 1024 * 1024) {
    showToast('File must be under 50MB.', 'error');
    return;
  }

  selectedFile = file;
  fileName.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(1)}MB)`;
  dropZone.querySelector('.drop-zone-content').style.display = 'none';
  filePreview.style.display = 'flex';
}

function clearFile() {
  selectedFile = null;
  fileInput.value = '';
  dropZone.querySelector('.drop-zone-content').style.display = '';
  filePreview.style.display = 'none';
}

// ════════════════════════════════════════════════════════
// LANGUAGE SWAP
// ════════════════════════════════════════════════════════
const langSwap = $('#lang-swap');
if (langSwap) {
  langSwap.addEventListener('click', () => {
    const source = $('#source-lang');
    const target = $('#target-lang');
    const sv = source.value;
    const tv = target.value;
    // Only swap if the value exists in both dropdowns
    if ([...source.options].some(o => o.value === tv) &&
      [...target.options].some(o => o.value === sv)) {
      source.value = tv;
      target.value = sv;
    }
    // Rotate animation
    langSwap.style.transform = `rotate(${(parseFloat(langSwap.dataset.rot || 0)) + 180}deg)`;
    langSwap.dataset.rot = (parseFloat(langSwap.dataset.rot || 0)) + 180;
  });
}

// ════════════════════════════════════════════════════════
// TRANSLATE SUBMISSION
// ════════════════════════════════════════════════════════
const translateBtn = $('#translate-btn');
const appInput = $('#app-input');
const appProcessing = $('#app-processing');
const appResult = $('#app-result');

if (translateBtn) {
  translateBtn.addEventListener('click', async () => {
    const activeTab = $('.tab-btn.active')?.dataset.tab;
    const targetLang = $('#target-lang').value;

    // Gather input
    let videoUrl = null;
    let file = null;

    if (activeTab === 'url') {
      videoUrl = $('#video-url').value.trim();
      if (!videoUrl) {
        showToast('Please paste a video URL.', 'error');
        return;
      }
    } else {
      file = selectedFile;
      if (!file) {
        showToast('Please select a video file.', 'error');
        return;
      }
    }

    // Switch to processing view
    setState('processing');

    // Build form data
    const formData = new FormData();
    if (file) {
      formData.append('file', file);
    } else {
      formData.append('url', videoUrl);
    }
    formData.append('target_language', targetLang);
    formData.append('source_language', $('#source-lang').value);

    try {
      // Submit job
      const res = await fetch(`${API_BASE}/api/jobs`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Server error' }));
        throw new Error(err.detail || 'Failed to start job');
      }

      const { job_id } = await res.json();

      // Stream progress via SSE
      streamProgress(job_id, targetLang);
    } catch (err) {
      showToast(err.message, 'error');
      setState('input');
    }
  });
}

function streamProgress(jobId, targetLang) {
  const log = $('#processing-log');
  const progressBar = $('#progress-bar');
  const stepText = $('#processing-step');
  log.innerHTML = '';

  const evtSource = new EventSource(`${API_BASE}/api/jobs/${jobId}`);
  let currentStep = 0;

  evtSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'progress') {
      const line = document.createElement('div');
      line.className = 'terminal-line';
      line.style.opacity = '1';
      line.textContent = data.message;
      log.appendChild(line);
      log.scrollTop = log.scrollHeight;

      // Update progress
      if (data.step) {
        currentStep = data.step;
        const pct = Math.round((currentStep / 6) * 100);
        progressBar.style.width = `${pct}%`;
        stepText.textContent = data.message;
      }
    }

    if (data.type === 'complete') {
      evtSource.close();
      progressBar.style.width = '100%';

      // Show result
      const video = $('#result-video');
      video.src = `${API_BASE}/api/jobs/${jobId}/result`;
      $('#result-meta').textContent = `Translated to ${targetLang} · Processed in ${data.elapsed || '—'}s`;
      $('#download-btn').href = `${API_BASE}/api/jobs/${jobId}/result`;

      // Swap skeleton for real video
      document.querySelector('.result-skeleton').style.display = 'none';
      document.querySelector('.result-content-wrap').style.display = 'block';

      setTimeout(() => setState('result'), 600);
    }

    if (data.type === 'error') {
      evtSource.close();
      showToast(data.message || 'Pipeline error occurred', 'error');
      setState('input');
    }
  };

  evtSource.onerror = () => {
    evtSource.close();
    showToast('Connection lost. Please try again.', 'error');
    setState('input');
  };
}

function setState(state) {
  const container = document.querySelector('.app-container');
  container.classList.remove('state-input', 'state-processing', 'state-result');
  container.classList.add(`state-${state}`);

  if (state !== 'input') {
    container.style.maxWidth = '100%';
  } else {
    container.style.maxWidth = '640px';
    // If going back to input, reset skeleton visibility
    const skeleton = document.querySelector('.result-skeleton');
    const contentWrap = document.querySelector('.result-content-wrap');
    if (skeleton && contentWrap) {
      skeleton.style.display = '';
      contentWrap.style.display = 'none';
    }
  }

  // Disable input controls during processing/result
  const isNotInput = state !== 'input';
  $('#file-input').disabled = isNotInput;
  $('#video-url').disabled = isNotInput;
  $('#translate-btn').disabled = isNotInput;
  $('#source-lang').disabled = isNotInput;
  $('#target-lang').disabled = isNotInput;
}

// New video button
const newVideoBtn = $('#new-video-btn');
if (newVideoBtn) {
  newVideoBtn.addEventListener('click', () => {
    clearFile();
    $('#video-url').value = '';
    setState('input');
  });
}

// ════════════════════════════════════════════════════════
// TOAST NOTIFICATIONS
// ════════════════════════════════════════════════════════
function showToast(message, type = 'info') {
  const existing = $('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button onclick="this.parentElement.remove()" aria-label="Dismiss">&times;</button>
  `;
  document.body.appendChild(toast);

  // Add styles if not present
  if (!$('#toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
      .toast {
        position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
        background: var(--surface); border: 1px solid var(--border);
        border-radius: 12px; padding: 12px 20px;
        display: flex; align-items: center; gap: 12px;
        font-size: .875rem; color: var(--text);
        box-shadow: 0 12px 40px rgba(0,0,0,.5);
        z-index: 10000; animation: toast-in .3s ease;
      }
      .toast-error { border-color: var(--red); }
      .toast button {
        background: none; border: none; color: var(--text-3);
        font-size: 1.2rem; cursor: pointer; padding: 0 4px;
      }
      @keyframes toast-in {
        from { opacity: 0; transform: translateX(-50%) translateY(12px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
      }
    `;
    document.head.appendChild(style);
  }

  setTimeout(() => { if (toast.parentElement) toast.remove(); }, 5000);
}

// ════════════════════════════════════════════════════════
// COMMAND PALETTE (⌘K / Ctrl+K)
// ════════════════════════════════════════════════════════
const cmdOverlay = $('#cmd-palette-overlay');
const cmdSearch = $('#cmd-search');
const cmdResultsContainer = $('#cmd-results');

const cmdActions = [
  {
    group: 'Navigation', items: [
      { label: 'Go to Home', icon: '🏠', action: () => scrollToSection('#hero') },
      { label: 'How it Works', icon: '⚡', action: () => scrollToSection('#how-it-works') },
      { label: 'See Demos', icon: '🎬', action: () => scrollToSection('#demos') },
      { label: 'Try Now — Free', icon: '🚀', action: () => scrollToSection('#app') },
      { label: 'View Pricing', icon: '💰', action: () => scrollToSection('#pricing') },
    ]
  },
  {
    group: 'Actions', items: [
      { label: 'Upload Video', icon: '📤', action: () => { scrollToSection('#app'); setTimeout(() => { $('#tab-upload')?.click(); }, 400); } },
      { label: 'Paste URL', icon: '🔗', action: () => { scrollToSection('#app'); setTimeout(() => { $('#tab-url')?.click(); }, 400); } },
      { label: 'Toggle Dark Mode', icon: '🌙', hint: 'Already dark ✓', action: () => { } },
    ]
  },
  {
    group: 'Languages', items: [
      { label: 'Translate to English', icon: '🇬🇧', action: () => setLang('English') },
      { label: 'Translate to Spanish', icon: '🇪🇸', action: () => setLang('Spanish') },
      { label: 'Translate to French', icon: '🇫🇷', action: () => setLang('French') },
      { label: 'Translate to German', icon: '🇩🇪', action: () => setLang('German') },
      { label: 'Translate to Hindi', icon: '🇮🇳', action: () => setLang('Hindi') },
      { label: 'Translate to Japanese', icon: '🇯🇵', action: () => setLang('Japanese') },
      { label: 'Translate to Chinese', icon: '🇨🇳', action: () => setLang('Chinese') },
      { label: 'Translate to Arabic', icon: '🇸🇦', action: () => setLang('Arabic') },
      { label: 'Translate to Korean', icon: '🇰🇷', action: () => setLang('Korean') },
      { label: 'Translate to Portuguese', icon: '🇧🇷', action: () => setLang('Portuguese') },
      { label: 'Translate to Italian', icon: '🇮🇹', action: () => setLang('Italian') },
    ]
  },
];

function setLang(lang) {
  const target = $('#target-lang');
  if (target) target.value = lang;
  scrollToSection('#app');
}

function scrollToSection(selector) {
  const el = $(selector);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Open / close
function openCmdPalette() {
  cmdOverlay.classList.add('open');
  cmdSearch.value = '';
  renderCmdResults('');
  setTimeout(() => cmdSearch.focus(), 100);
}
function closeCmdPalette() {
  cmdOverlay.classList.remove('open');
}

// Keyboard shortcut
document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    if (cmdOverlay.classList.contains('open')) {
      closeCmdPalette();
    } else {
      openCmdPalette();
    }
  }
  if (e.key === 'Escape' && cmdOverlay.classList.contains('open')) {
    closeCmdPalette();
  }
});

// Close on overlay click
if (cmdOverlay) {
  cmdOverlay.addEventListener('click', (e) => {
    if (e.target === cmdOverlay) closeCmdPalette();
  });
}

// Search filtering
let activeIndex = 0;
if (cmdSearch) {
  cmdSearch.addEventListener('input', () => {
    renderCmdResults(cmdSearch.value);
  });

  // Arrow key navigation
  cmdSearch.addEventListener('keydown', (e) => {
    const items = $$('.cmd-item');
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeIndex = Math.min(activeIndex + 1, items.length - 1);
      updateActiveItem(items);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeIndex = Math.max(activeIndex - 1, 0);
      updateActiveItem(items);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (items[activeIndex]) items[activeIndex].click();
    }
  });
}

function updateActiveItem(items) {
  items.forEach((item, i) => {
    item.classList.toggle('active', i === activeIndex);
    if (i === activeIndex) item.scrollIntoView({ block: 'nearest' });
  });
}

function renderCmdResults(query) {
  if (!cmdResultsContainer) return;
  const q = query.toLowerCase().trim();
  activeIndex = 0;
  let html = '';

  cmdActions.forEach(group => {
    const filtered = group.items.filter(item =>
      !q || item.label.toLowerCase().includes(q)
    );
    if (filtered.length === 0) return;

    html += `<div class="cmd-group-label">${group.group}</div>`;
    filtered.forEach((item, idx) => {
      html += `
        <div class="cmd-item" data-group="${group.group}" data-label="${item.label}">
          <div class="cmd-item-icon">${item.icon}</div>
          <span class="cmd-item-text">${item.label}</span>
          ${item.hint ? `<span class="cmd-item-hint">${item.hint}</span>` : ''}
        </div>
      `;
    });
  });

  if (!html) {
    html = `<div style="padding: 32px; text-align: center; color: var(--text-3); font-size: .875rem;">No results for "${query}"</div>`;
  }

  cmdResultsContainer.innerHTML = html;

  // Bind click handlers
  $$('.cmd-item').forEach((el, idx) => {
    el.addEventListener('click', () => {
      const label = el.dataset.label;
      const group = el.dataset.group;
      const groupData = cmdActions.find(g => g.group === group);
      const itemData = groupData?.items.find(i => i.label === label);
      if (itemData) {
        closeCmdPalette();
        itemData.action();
      }
    });
    el.addEventListener('mouseenter', () => {
      activeIndex = idx;
      updateActiveItem($$('.cmd-item'));
    });
  });

  // Highlight first
  const items = $$('.cmd-item');
  if (items[0]) items[0].classList.add('active');
}

// ── CMD palette trigger button in nav ───────────────────
const cmdTrigger = $('#cmd-trigger');
if (cmdTrigger) {
  cmdTrigger.addEventListener('click', (e) => {
    e.preventDefault();
    openCmdPalette();
  });
}

// ════════════════════════════════════════════════════════
// FREE QUOTA TRACKING (localStorage)
// ════════════════════════════════════════════════════════
function getUsedVideos() {
  return parseInt(localStorage.getItem('vv_used') || '0', 10);
}
function incrementUsedVideos() {
  localStorage.setItem('vv_used', (getUsedVideos() + 1).toString());
}
