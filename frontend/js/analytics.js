document.addEventListener("DOMContentLoaded", async () => {
    hydrateUser();
    const [overview, domainTime, solved, coverage] = await Promise.all([
        fetchJson("/analytics/overview", {}),
        fetchJson("/analytics/domain-time?period=30", { series: [], data: [] }),
        fetchJson("/analytics/problems-solved?period=30", []),
        fetchJson("/analytics/skill-coverage", [])
    ]);
    renderCards(overview);
    renderDomainTime(domainTime);
    renderSolved(solved);
    renderCoverage(coverage);
});

function hydrateUser() {
    const user = getUser();
    if (!user) return;
    document.getElementById("user-name").textContent = user.name;
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

function renderCards(data) {
    const cards = [
        ["Total Study", `${data.total_minutes || 0} min`],
        ["Active Domains", data.domains_active || 0],
        ["Topics Completed", data.problems_solved || 0],
        ["Consistency", `${data.consistency_pct || 0}%`]
    ];
    document.getElementById("analytics-cards").innerHTML = cards.map(([label, value]) => `<div class="stat-box glass-panel"><div class="stat-info"><span class="stat-val">${value}</span><span class="stat-lbl">${label}</span></div></div>`).join("");
}

function renderDomainTime(payload) {
    const labels = payload.data.map(row => row.date);
    const colors = ["#58a6ff", "#3fb950", "#bc8cff", "#d29922", "#f85149", "#2dd4bf"];
    new Chart(document.getElementById("domain-time-chart"), {
        type: "bar",
        data: { labels, datasets: payload.series.map((name, i) => ({ label: name, data: payload.data.map(row => row[name] || 0), backgroundColor: colors[i % colors.length] })) },
        options: { responsive: true, scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } } }
    });
}

function renderSolved(rows) {
    new Chart(document.getElementById("solved-chart"), {
        type: "line",
        data: { labels: rows.map(row => row.date), datasets: [{ label: "Solved", data: rows.map(row => row.count), borderColor: "#3fb950", backgroundColor: "rgba(63,185,80,.16)", fill: true, tension: .3 }] },
        options: { responsive: true, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
    });
}

function renderCoverage(rows) {
    new Chart(document.getElementById("coverage-chart"), {
        type: "radar",
        data: { labels: rows.map(row => row.domain), datasets: [{ label: "Coverage %", data: rows.map(row => row.coverage), borderColor: "#bc8cff", backgroundColor: "rgba(188,140,255,.18)" }] },
        options: { responsive: true, scales: { r: { suggestedMin: 0, suggestedMax: 100 } } }
    });
}
