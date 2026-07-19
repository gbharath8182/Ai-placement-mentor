$ErrorActionPreference = "Stop"
$repoRoot = (Get-Location).Path
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$js = @'
async function miPageLoadDomains() {
    miShowPanel("mi-loading");
    try {
        const res = await authFetch("/domains/with-details");
        if (!res.ok) {
            console.error("Failed to load domains with details");
            miShowPanel("mi-domain-select");
            return;
        }
        const domains = await res.json();
        const grid = document.getElementById("mi-domain-grid");
        const empty = document.getElementById("mi-domain-empty");
        grid.innerHTML = "";

        if (!domains || domains.length === 0) {
            empty.classList.remove("hidden");
            miShowPanel("mi-domain-select");
            return;
        }
        empty.classList.add("hidden");

        domains.forEach((domain) => {
            const card = document.createElement("div");
            card.className = "mi-domain-card";
            card.innerHTML = `
                <h3>${domain.title || domain.slug}</h3>
                <p>${domain.description || ""}</p>
            `;
            card.addEventListener("click", () => {
                miState.domainSlug = domain.slug;
                miShowPanel("mi-mode-select");
            });
            grid.appendChild(card);
        });

        miShowPanel("mi-domain-select");
    } catch (e) {
        console.error("Error loading domains:", e);
        miShowPanel("mi-domain-select");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    miPageLoadDomains();

    document.querySelectorAll(".mi-mode-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            miStartInterview(btn.getAttribute("data-mode"));
        });
    });

    document.getElementById("mi-submit-btn").addEventListener("click", miSubmitAnswer);
    document.getElementById("mi-explain-more-btn").addEventListener("click", miExplainMore);
    document.getElementById("mi-next-btn").addEventListener("click", miGoNext);

    document.getElementById("mi-restart-btn").addEventListener("click", () => {
        miShowPanel("mi-mode-select");
    });

    document.getElementById("mi-back-to-domains-1").addEventListener("click", () => {
        miShowPanel("mi-domain-select");
    });
    document.getElementById("mi-back-to-domains-2").addEventListener("click", () => {
        miShowPanel("mi-domain-select");
    });
});
'@

$target = Join-Path $repoRoot "frontend\js\mock-interview-page.js"
[System.IO.File]::WriteAllText($target, $js, $utf8NoBom)
Write-Host "Wrote: frontend\js\mock-interview-page.js"