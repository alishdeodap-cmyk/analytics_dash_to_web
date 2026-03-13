/* Analytics Hub — Main JS */

// ── Theme switcher ───────────────────────────────────────────
function setTheme(theme) {
    document.body.classList.toggle('light', theme === 'light');
    localStorage.setItem('ah-theme', theme);
    document.getElementById('themeDark').classList.toggle('active', theme === 'dark');
    document.getElementById('themeLight').classList.toggle('active', theme === 'light');
}
// Apply saved theme immediately (default: dark)
(function () {
    const saved = localStorage.getItem('ah-theme') || 'light';
    setTheme(saved);
})();

// ── Sidebar toggle (mobile) ──────────────────────────────────
const sidebar = document.getElementById('sidebar');
const toggle  = document.getElementById('sidebarToggle');
if (toggle && sidebar) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', (e) => {
        if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggle) {
            sidebar.classList.remove('open');
        }
    });
}

// ── Settings tab switcher ────────────────────────────────────
document.querySelectorAll('.settings-nav-item[data-panel]').forEach(item => {
    item.addEventListener('click', () => {
        const target = item.dataset.panel;
        document.querySelectorAll('.settings-nav-item').forEach(i => i.classList.remove('active'));
        document.querySelectorAll('.settings-panel').forEach(p => p.classList.remove('active'));
        item.classList.add('active');
        const panel = document.getElementById(target);
        if (panel) panel.classList.add('active');
    });
});

// ── Auto-dismiss flash messages ──────────────────────────────
document.querySelectorAll('.flash').forEach(flash => {
    setTimeout(() => {
        flash.style.transition = 'opacity 0.4s ease';
        flash.style.opacity = '0';
        setTimeout(() => flash.remove(), 400);
    }, 4000);
});

// ── Confirm delete dialogs ───────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', (e) => {
        if (!confirm(btn.dataset.confirm)) e.preventDefault();
    });
});

// ── Highlight active nav item from URL ──────────────────────
// (handled server-side via Jinja — this is a fallback)

// ── Dashboard card open-in-portal ───────────────────────────
document.querySelectorAll('.dashboard-card[data-url]').forEach(card => {
    card.addEventListener('click', () => {
        window.location.href = card.dataset.url;
    });
});
