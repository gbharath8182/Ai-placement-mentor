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
                miPageShowModeStep();
            });
            grid.appendChild(card);
        });

        miPageShowDomainStep();
        miShowPanel("mi-domain-select");
    } catch (e) {
        console.error("Error loading domains:", e);
        miShowPanel("mi-domain-select");
    }
}

function miPageShowDomainStep() {
    document.getElementById("mi-domain-grid-wrap").classList.remove("hidden");
    document.getElementById("mi-mode-grid-wrap").classList.add("hidden");
}

function miPageShowModeStep() {
    document.getElementById("mi-domain-grid-wrap").classList.add("hidden");
    document.getElementById("mi-mode-grid-wrap").classList.remove("hidden");
}

async function miPageEndInterviewNow() {
    const btn = document.getElementById("mi-end-btn");
    btn.disabled = true;
    btn.textContent = "Calculating score...";
    try {
        const res = await authFetch("/mock-interview/end", {
            method: "POST",
            body: { session_id: miState.sessionId }
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            alert("Could not end interview: " + (err.detail || "Server error"));
            return;
        }
        const data = await res.json();
        miRenderSummary(data.summary);
    } catch (e) {
        console.error("End interview error:", e);
        alert("Connection error ending interview.");
    } finally {
        btn.disabled = false;
        btn.textContent = "End Interview Now & See Score";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    miPageLoadDomains();

    document.getElementById("mi-back-to-domains").addEventListener("click", () => {
        miPageShowDomainStep();
    });

    document.querySelectorAll(".mi-mode-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            miStartInterview(btn.getAttribute("data-mode"));
        });
    });

    document.getElementById("mi-submit-btn").addEventListener("click", miSubmitAnswer);
    document.getElementById("mi-explain-more-btn").addEventListener("click", miExplainMore);
    document.getElementById("mi-next-btn").addEventListener("click", miGoNext);
    document.getElementById("mi-end-btn").addEventListener("click", miPageEndInterviewNow);

    document.getElementById("mi-restart-btn").addEventListener("click", () => {
        miPageShowModeStep();
        miShowPanel("mi-domain-select");
    });

    document.getElementById("mi-new-domain-btn").addEventListener("click", () => {
        miPageShowDomainStep();
        miShowPanel("mi-domain-select");
    });
});