document.addEventListener("DOMContentLoaded", async () => {
    hydrateUser();
    const [streak, heatmap, timeSpent, coverage] = await Promise.all([
        fetchJson("/activity/streak", { current_streak: 0, longest_streak: 0 }),
        fetchJson(`/activity/heatmap?year=${new Date().getFullYear()}`, []),
        fetchJson("/activity/time-spent?period=30&aggregation=daily", []),
        fetchJson("/analytics/skill-coverage", [])
    ]);
    renderStreak(streak);
    renderHeatmap(heatmap);
    renderStudyChart(timeSpent);
    renderCoverage(coverage);
});

function hydrateUser() {
    const user = getUser();
    if (!user) return;
    document.getElementById("user-name").textContent = user.name;
    document.getElementById("profile-name").textContent = user.name;
    document.getElementById("profile-meta").textContent = `${user.profile.experience_level} learner`;
    const badge = document.getElementById("user-exp-badge");
    badge.textContent = user.profile.experience_level;
    badge.className = `experience-tag exp-${user.profile.experience_level}`;
}

async function fetchJson(url, fallback) {
    try {
        const res = await authFetch(url);
        return res.ok ? await res.json() : fallback;
    } catch {
        return fallback;
    }
}

function renderStreak(streak) {
    document.getElementById("current-streak").textContent = streak.current_streak || 0;
    document.getElementById("longest-streak").textContent = `Longest: ${streak.longest_streak || 0} days`;
}

function renderHeatmap(rows) {
    const values = Object.fromEntries(rows.map(row => [row.date, row.minutes_spent]));
    const today = new Date();
    const start = new Date(today);
    start.setDate(today.getDate() - 181);
    const wrap = document.getElementById("heatmap-wrap");
    let cells = "";
    for (let date = new Date(start); date <= today; date.setDate(date.getDate() + 1)) {
        const iso = date.toISOString().slice(0, 10);
        const minutes = values[iso] || 0;
        const level = minutes >= 90 ? 4 : minutes >= 45 ? 3 : minutes >= 15 ? 2 : minutes > 0 ? 1 : 0;
        cells += `<rect class="heat-cell level-${level}" width="10" height="10" x="${Math.floor((new Date(date) - start) / 86400000 / 7) * 14}" y="${date.getDay() * 14}"><title>${iso}: ${minutes} min</title></rect>`;
    }
    wrap.innerHTML = `<svg class="heatmap-svg" viewBox="0 0 378 98" role="img" aria-label="Learning activity heatmap">${cells}</svg>`;
}

function renderStudyChart(rows) {
    const ctx = document.getElementById("study-chart");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: rows.map(row => row.label),
            datasets: [{ label: "Minutes", data: rows.map(row => row.minutes_spent), borderColor: "#58a6ff", backgroundColor: "rgba(88,166,255,.16)", fill: true, tension: .35 }]
        },
        options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
}

function renderCoverage(rows) {
    const body = document.getElementById("profile-progress-body");
    body.innerHTML = rows.map(row => `
        <tr>
            <td>${escapeHtml(row.domain)}</td>
            <td>${row.completed} / ${row.total}</td>
            <td><div class="coverage-bar"><span style="width:${row.coverage}%"></span></div>${row.coverage}%</td>
        </tr>
    `).join("") || `<tr><td colspan="3">No progress yet.</td></tr>`;
}

function escapeHtml(text) {
    return String(text || "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}
