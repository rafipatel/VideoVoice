// app.js — Frontend interactions for VideoVoice landing page

// ── Reveal on scroll ─────────────────────────────────────────────
const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        // Stagger sibling reveals
        const siblings = [...entry.target.parentElement.querySelectorAll('.reveal:not(.visible)')];
        const delay = siblings.indexOf(entry.target) * 80;
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, delay);
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12 }
);

document.querySelectorAll('.reveal').forEach((el) => revealObserver.observe(el));

// ── Gradio iframe health check ────────────────────────────────────
const iframe = document.getElementById('gradio-iframe');
const fallback = document.getElementById('demo-fallback');

if (iframe) {
  iframe.addEventListener('error', () => {
    iframe.style.display = 'none';
    fallback.style.display = 'flex';
  });

  // Timeout: if iframe hasn't loaded in 4s, show fallback
  const iframeTimeout = setTimeout(() => {
    try {
      // If cross-origin, accessing contentDocument throws — that means it loaded
      const doc = iframe.contentDocument;
      if (!doc || doc.body === null) {
        iframe.style.display = 'none';
        fallback.style.display = 'flex';
      }
    } catch (_) {
      // Cross-origin = loaded fine, do nothing
    }
  }, 4000);

  iframe.addEventListener('load', () => clearTimeout(iframeTimeout));
}

// ── Smooth active nav highlight ───────────────────────────────────
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-links a');

const navObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        navLinks.forEach((link) => {
          link.style.color = link.getAttribute('href') === `#${entry.target.id}` ? '#a78bfa' : '';
        });
      }
    });
  },
  { threshold: 0.5 }
);

sections.forEach((s) => navObserver.observe(s));
