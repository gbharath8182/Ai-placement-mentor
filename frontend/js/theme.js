(function () {
    function getIcon(isLight) {
        if (isLight) {
            return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
        }
        return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    }

    function applyIcon() {
        var btn = document.getElementById('theme-toggle');
        if (!btn) return;
        var isLight = document.documentElement.classList.contains('light-theme');
        const workspace = document.body?.classList.contains('app-page') || document.body?.classList.contains('auth-premium');
        if (workspace) btn.textContent = isLight ? 'Dark appearance' : 'Light appearance';
        else btn.innerHTML = getIcon(isLight);
        btn.setAttribute('aria-label', isLight ? 'Switch to dark theme' : 'Switch to light theme');
        btn.setAttribute('aria-pressed', String(isLight));
        btn.title = btn.getAttribute('aria-label');
        btn.querySelector('svg')?.setAttribute('aria-hidden', 'true');
    }

    function toggleTheme() {
        document.documentElement.classList.toggle('light-theme');
        var isLight = document.documentElement.classList.contains('light-theme');
        try {
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
        } catch {}
        applyIcon();
        window.dispatchEvent(new CustomEvent('appearancechange'));
    }

    function restoreTheme() {
        try {
            document.documentElement.classList.toggle('light-theme', localStorage.getItem('theme') === 'light');
        } catch {}
        applyIcon();
    }

    restoreTheme();
    window.addEventListener('storage', function (event) {
        if (event.key === 'theme' || event.key === null) restoreTheme();
    });

    function initialize() {
        restoreTheme();
        applyIcon();
        var btn = document.getElementById('theme-toggle');
        if (btn) {
            btn.addEventListener('click', toggleTheme);
        }
        const toggle = document.getElementById('ai-panel-toggle');
        const panel = document.getElementById('ai-panel');
        if (!toggle || !panel) return;
        const mobile = window.matchMedia(document.body.classList.contains('app-page') ? '(max-width: 1350px)' : '(max-width: 1120px)');
        let expanded = false;

        function updatePanel() {
            const visible = !mobile.matches || expanded;
            if (!visible && panel.contains(document.activeElement)) toggle.focus();
            panel.hidden = !visible;
            panel.classList.toggle('is-open', visible);
            toggle.setAttribute('aria-expanded', String(visible));
            toggle.textContent = visible ? 'Close AI tutor' : 'Open AI tutor';
        }

        toggle.addEventListener('click', function () {
            expanded = !expanded;
            updatePanel();
            if (expanded && mobile.matches) panel.scrollIntoView({ behavior: 'auto', block: 'start' });
        });
        panel.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && mobile.matches) {
                expanded = false;
                updatePanel();
                toggle.focus();
            }
        });
        mobile.addEventListener('change', function () {
            expanded = false;
            updatePanel();
        });
        updatePanel();
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
    else initialize();
})();
