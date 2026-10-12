(function () {
    const groups = [
        ['Workspace', [['Dashboard', '/dashboard'], ['Learning paths', '/roadmap'], ['Analytics', '/analytics']]],
        ['Study', [['Curriculum', '/learn'], ['Code workspace', '/playground'], ['Reference library', '/cheatsheets'], ['Aptitude practice', '/aptitude']]],
        ['Career', [['Mock interviews', '/mock-interview'], ['Resume studio', '/resume']]],
    ];
    const path = window.location.pathname;
    function readUser() {
        try { return typeof getUser === 'function' ? getUser() : JSON.parse(localStorage.getItem('user') || 'null'); }
        catch { return null; }
    }
    const user = readUser();

    function element(tag, className, text) {
        const result = document.createElement(tag);
        if (className) result.className = className;
        if (text !== undefined) result.textContent = text;
        return result;
    }

    function brand(destination) {
        const link = element('a', 'workspace-brand');
        link.href = destination;
        link.append(element('span', 'workspace-monogram', 'AM'), element('span', 'workspace-brand-name', 'AI Placement Mentor'));
        return link;
    }

    function authLayout() {
        const card = document.querySelector('.auth-card');
        if (!card) return;
        document.body.classList.add('auth-premium');
        const layout = element('main', 'auth-layout');
        const story = element('section', 'auth-story');
        const copy = element('div', 'auth-story-copy');
        copy.append(element('p', 'workspace-eyebrow', 'A focused learning environment'), element('h1', '', 'Understand deeply.\nPractice deliberately.'), element('p', '', 'Work through structured lessons, test your reasoning and prepare for the conversations that matter.'));
        const steps = element('div', 'auth-story-steps');
        ['01 / Learn the fundamentals', '02 / Put understanding into practice', '03 / Prepare with honest feedback'].forEach(text => steps.appendChild(element('p', '', text)));
        story.append(brand('/'), copy, steps);
        card.before(layout);
        layout.append(story, card);
        card.id = card.id || 'main-content';
        const oldBrand = card.querySelector('.auth-brand-row .nav-brand');
        if (oldBrand) oldBrand.replaceWith(brand('/'));
        card.querySelector('.logo-icon')?.remove();
    }

    function workspace() {
        const previous = document.querySelector('.app-fallback-nav') || (path === '/learn' && user ? document.querySelector('.dashboard-nav') : null);
        if (!previous) return;
        document.body.classList.add('app-page');
        const sidebar = element('aside', 'workspace-sidebar');
        sidebar.id = 'workspace-sidebar';
        sidebar.setAttribute('aria-label', 'Workspace navigation');
        const close = element('button', 'workspace-close', 'Close navigation');
        close.type = 'button';
        sidebar.append(brand('/dashboard'), close);
        const navigation = element('nav', 'workspace-navigation');
        navigation.setAttribute('aria-label', 'Primary');
        let currentLabel = path.startsWith('/topic/') ? 'Lesson' : 'Workspace';
        groups.forEach(([heading, entries]) => {
            const section = element('div', 'workspace-nav-group');
            section.appendChild(element('p', 'workspace-nav-label', heading));
            entries.forEach(([label, href]) => {
                const link = element('a', 'workspace-nav-link', label);
                link.href = href;
                if (path === href || (href === '/learn' && path.startsWith('/topic/'))) {
                    link.setAttribute('aria-current', 'page');
                    if (!path.startsWith('/topic/')) currentLabel = label;
                }
                section.appendChild(link);
            });
            navigation.appendChild(section);
        });
        const footer = element('div', 'workspace-account');
        const profile = element('a', 'workspace-profile');
        profile.href = user ? '/profile' : '/login';
        const name = element('span', '', user?.name || 'Guest reader');
        name.id = 'user-name';
        const level = element('span', 'experience-tag', user?.profile?.experience_level || 'Public curriculum');
        level.id = 'user-exp-badge';
        profile.append(name, level);
        if (path === '/profile') { profile.setAttribute('aria-current', 'page'); currentLabel = 'Profile'; }
        const theme = element('button', 'workspace-appearance theme-toggle', 'Appearance');
        theme.id = 'theme-toggle';
        theme.type = 'button';
        footer.append(profile, theme);
        if (user) {
            const logout = element('button', 'workspace-signout', 'Sign out');
            logout.type = 'button';
            logout.addEventListener('click', () => logoutUser());
            footer.appendChild(logout);
        } else {
            const login = element('a', 'workspace-signout', 'Sign in');
            login.href = '/login';
            footer.appendChild(login);
        }
        sidebar.append(navigation, footer);
        previous.replaceWith(sidebar);
        const main = document.querySelector('main') || document.querySelector('.cs-container');
        if (!main) return;
        if (main.tagName !== 'MAIN') main.setAttribute('role', 'main');
        main.id = main.id || 'main-content';
        if (!document.querySelector('.skip-link')) {
            const skip = element('a', 'skip-link', 'Skip to content');
            skip.href = '#' + main.id;
            document.body.prepend(skip);
        }
        const topbar = element('header', 'workspace-topbar');
        const menu = element('button', 'workspace-menu', 'Menu');
        menu.type = 'button';
        menu.setAttribute('aria-controls', sidebar.id);
        menu.setAttribute('aria-expanded', 'false');
        const breadcrumb = element('p', 'workspace-breadcrumb');
        breadcrumb.append(element('span', '', 'Workspace'), element('span', 'workspace-divider', '/'), element('strong', '', currentLabel));
        const home = element('a', 'workspace-home-link', 'Visit homepage');
        home.href = '/';
        topbar.append(menu, breadcrumb, home);
        main.before(topbar);
        const backdrop = element('button', 'workspace-backdrop');
        backdrop.type = 'button';
        backdrop.setAttribute('aria-label', 'Close navigation');
        backdrop.hidden = true;
        document.body.appendChild(backdrop);
        const mobile = window.matchMedia('(max-width: 960px)');
        let open = false;

        function update(focus = false) {
            const visible = !mobile.matches || open;
            sidebar.inert = !visible;
            sidebar.setAttribute('aria-hidden', String(!visible));
            document.body.classList.toggle('workspace-nav-open', mobile.matches && open);
            menu.setAttribute('aria-expanded', String(mobile.matches && open));
            backdrop.hidden = !mobile.matches || !open;
            if (focus) (open ? close : menu).focus();
        }

        menu.addEventListener('click', () => { open = !open; update(true); });
        [close, backdrop].forEach(button => button.addEventListener('click', () => { open = false; update(true); }));
        document.addEventListener('keydown', event => {
            if (!mobile.matches || !open) return;
            if (event.key === 'Escape') { open = false; update(true); }
            if (event.key === 'Tab') {
                const focusable = [...sidebar.querySelectorAll('a, button')].filter(item => !item.hidden && !item.disabled);
                const first = focusable[0];
                const last = focusable.at(-1);
                if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
                else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
            }
        });
        mobile.addEventListener('change', () => { open = false; update(); });
        update();
        function updateCharts() {
            if (!window.Chart) return;
            const styles = getComputedStyle(document.body);
            const color = styles.getPropertyValue('--text-muted').trim();
            const border = styles.getPropertyValue('--border-color').trim();
            Chart.defaults.color = color;
            Chart.defaults.borderColor = border;
            Chart.defaults.font.family = styles.getPropertyValue('--font-sans').trim();
            Object.values(Chart.instances).forEach(chart => {
                Object.values(chart.options.scales || {}).forEach(scale => {
                    if (scale.ticks) scale.ticks.color = color;
                    if (scale.grid) scale.grid.color = border;
                    if (scale.pointLabels) scale.pointLabels.color = color;
                });
                chart.update('none');
            });
        }
        updateCharts();
        window.addEventListener('appearancechange', updateCharts);
    }

    if (document.body.classList.contains('auth-container')) authLayout();
    else workspace();
})();
