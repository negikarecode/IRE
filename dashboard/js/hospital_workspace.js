/* Claims Queue Pagination State (Supported for Future Pagination, UI Not Rendered Yet) */
const claimsPaginationState = {
    currentPage: 1,
    pageSize: 10,
    totalItems: 84
};

/* Master Claims Queue Data Set (Workflow-Oriented) */
const masterClaimsData = [
    {
        id: "CLM-2026-90124",
        patient: "Sunita Verma",
        insurance: "Star Health Insurance",
        stageKey: "NEEDS_REVIEW",
        stageLabel: "Needs Review",
        risk: "HIGH",
        revenue: "₹1,29,000.00",
        lastUpdated: "10 mins ago"
    },
    {
        id: "CLM-90128",
        patient: "Amitabh Sharma",
        insurance: "HDFC ERGO Health",
        stageKey: "MISSING_DOCS",
        stageLabel: "Missing Documents",
        risk: "MEDIUM",
        revenue: "₹34,500.00",
        lastUpdated: "25 mins ago"
    },
    {
        id: "CLM-88192",
        patient: "Rajesh Patel",
        insurance: "ICICI Lombard General",
        stageKey: "DENIED",
        stageLabel: "Denied",
        risk: "HIGH",
        revenue: "₹1,85,000.00",
        lastUpdated: "1 hour ago"
    },
    {
        id: "CLM-77104",
        patient: "Priya Sundaram",
        insurance: "Max Bupa (Niva Bupa)",
        stageKey: "NEEDS_REVIEW",
        stageLabel: "Needs Review",
        risk: "MEDIUM",
        revenue: "₹45,000.00",
        lastUpdated: "2 hours ago"
    },
    {
        id: "CLM-66019",
        patient: "Vikram Malhotra",
        insurance: "Ayushman Bharat (PM-JAY)",
        stageKey: "READY",
        stageLabel: "Ready to Submit",
        risk: "LOW",
        revenue: "₹2,10,000.00",
        lastUpdated: "3 hours ago"
    },
    {
        id: "CLM-55012",
        patient: "Ananya Roy",
        insurance: "Star Health Insurance",
        stageKey: "SUBMITTED",
        stageLabel: "Submitted",
        risk: "LOW",
        revenue: "₹88,000.00",
        lastUpdated: "5 hours ago"
    },
    {
        id: "CLM-44091",
        patient: "Suresh Gupta",
        insurance: "HDFC ERGO Health",
        stageKey: "READY",
        stageLabel: "Ready to Submit",
        risk: "LOW",
        revenue: "₹1,45,000.00",
        lastUpdated: "Yesterday"
    }
];

document.addEventListener("DOMContentLoaded", () => {
    const navItems = document.querySelectorAll(".nav-item");
    const views = document.querySelectorAll(".dashboard-view");
    const pageTitle = document.getElementById("page-title");

    const tabTitles = {
        "dashboard": "Dashboard",
        "upload-claim": "Upload Claim Documents",
        "claims": "Claims Work Queue",
        "claim-review": "Unified Claim Review Workspace",
        "appeals": "Appeals Case Manager",
        "settings": "Hospital Facility Settings"
    };

    function switchTab(tabId) {
        navItems.forEach(item => {
            if (item.dataset.tab === tabId) {
                item.classList.add("active");
            } else {
                item.classList.remove("active");
            }
        });

        views.forEach(view => {
            if (view.id === `view-${tabId}`) {
                view.classList.add("active");
            } else {
                view.classList.remove("active");
            }
        });

        if (tabTitles[tabId]) {
            pageTitle.textContent = tabTitles[tabId];
        }

        if (tabId === "claims") {
            renderClaimsQueue("ALL");
        }
    }

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.dataset.tab;
            window.location.hash = tabId;
            switchTab(tabId);
        });
    });

    const initialHash = window.location.hash.replace("#", "") || "dashboard";
    switchTab(initialHash);

    /* Setup Drag & Drop Handlers on Upload Card */
    const dropboxCard = document.getElementById("dropbox-card");
    if (dropboxCard) {
        ["dragenter", "dragover"].forEach(eventName => {
            dropboxCard.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropboxCard.classList.add("dragover");
            }, false);
        });

        ["dragleave", "drop"].forEach(eventName => {
            dropboxCard.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropboxCard.classList.remove("dragover");
            }, false);
        });

        dropboxCard.addEventListener("drop", (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                handleDedicatedUpload(files);
            }
        });
    }

    // Initial render of claims queue table
    renderClaimsQueue("ALL");
});

/* Filter Claims Queue via Filter Chips */
let currentClaimsFilter = "ALL";

function filterClaimsQueue(categoryKey, chipBtn) {
    currentClaimsFilter = categoryKey;
    const chips = document.querySelectorAll(".filter-chip");
    chips.forEach(c => c.classList.remove("active"));
    if (chipBtn) chipBtn.classList.add("active");

    renderClaimsQueue(categoryKey);
}

function renderClaimsQueue(filterKey) {
    const tbody = document.getElementById("claims-queue-tbody");
    if (!tbody) return;

    let filtered = masterClaimsData;
    if (filterKey !== "ALL") {
        filtered = masterClaimsData.filter(item => item.stageKey === filterKey);
    }

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 32px; color: #64748b;">No claims found for this filter state.</td></tr>`;
        return;
    }

    let html = "";
    filtered.forEach(claim => {
        // Stage Badge Styling (Color used sparingly — only highlight claims needing attention)
        let stageBadge = `<span class="badge" style="background: rgba(255,255,255,0.06); color: #94a3b8;">${claim.stageLabel}</span>`;
        if (claim.stageKey === "NEEDS_REVIEW") {
            stageBadge = `<span class="badge badge-warning">Needs Review</span>`;
        } else if (claim.stageKey === "MISSING_DOCS") {
            stageBadge = `<span class="badge badge-warning" style="border-color: rgba(245,158,11,0.5);">Missing Docs</span>`;
        } else if (claim.stageKey === "DENIED") {
            stageBadge = `<span class="badge badge-danger">Denied</span>`;
        }

        // Risk Level Styling
        let riskBadge = `<span class="badge" style="background: rgba(255,255,255,0.05); color: #64748b;">${claim.risk}</span>`;
        if (claim.risk === "HIGH") {
            riskBadge = `<span class="badge badge-danger">HIGH RISK</span>`;
        } else if (claim.risk === "MEDIUM") {
            riskBadge = `<span class="badge badge-warning">MEDIUM</span>`;
        }

        html += `
            <tr>
                <td class="font-mono" style="color: var(--accent-cyan); font-weight: 600;">#${claim.id}</td>
                <td style="font-weight: 500; color: #ffffff;">${claim.patient}</td>
                <td style="color: #94a3b8;">${claim.insurance}</td>
                <td>${stageBadge}</td>
                <td>${riskBadge}</td>
                <td class="font-mono" style="font-weight: 600; color: #ffffff;">${claim.revenue}</td>
                <td style="color: #64748b; font-size: 0.82rem;">${claim.lastUpdated}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="openMergedClaimReview('${claim.id}')">Open Review →</button>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

/* Open Merged Claim Review Workflow */
function openMergedClaimReview(claimId) {
    window.location.hash = "claim-review";
    const navItems = document.querySelectorAll(".nav-item");
    const views = document.querySelectorAll(".dashboard-view");
    const pageTitle = document.getElementById("page-title");

    navItems.forEach(item => item.classList.remove("active"));

    views.forEach(view => {
        if (view.id === "view-claim-review") view.classList.add("active");
        else view.classList.remove("active");
    });

    if (pageTitle) {
        pageTitle.textContent = `Unified Claim Review — #${claimId}`;
    }
}

function triggerFileUpload() {
    const input = document.getElementById("dashboard-file-input");
    if (input) input.click();
}

function triggerDedicatedUpload() {
    const input = document.getElementById("dedicated-file-input");
    if (input) input.click();
}

function handleDashboardUpload(files) {
    if (files && files.length > 0) {
        window.location.hash = "upload-claim";
        const navItems = document.querySelectorAll(".nav-item");
        const views = document.querySelectorAll(".dashboard-view");
        navItems.forEach(i => i.classList.remove("active"));
        views.forEach(v => {
            if (v.id === "view-upload-claim") v.classList.add("active");
            else v.classList.remove("active");
        });
        handleDedicatedUpload(files);
    }
}

function handleDedicatedUpload(files) {
    if (!files || files.length === 0) return;

    const timelineBox = document.getElementById("upload-timeline-box");
    const percentLabel = document.getElementById("processing-progress-percent");
    const titleLabel = document.getElementById("file-processing-title");

    if (timelineBox) timelineBox.style.display = "block";
    if (titleLabel) titleLabel.textContent = `Processing ${files.length} Document(s): ${files[0].name}...`;

    const steps = [
        { id: "step-ocr", icon: "icon-ocr", label: "✓ OCR Started", pct: "20%", delay: 400 },
        { id: "step-extract", icon: "icon-extract", label: "✓ Extracting Clinical Data", pct: "40%", delay: 900 },
        { id: "step-rules", icon: "icon-rules", label: "✓ Running Insurance Rules", pct: "70%", delay: 1400 },
        { id: "step-ai", icon: "icon-ai", label: "✓ AI Reviewing Claim", pct: "90%", delay: 1900 },
        { id: "step-completed", icon: "icon-completed", label: "✓ Completed", pct: "100%", delay: 2400 }
    ];

    steps.forEach(s => {
        const el = document.getElementById(s.id);
        const iconEl = document.getElementById(s.icon);
        if (el) { el.className = "timeline-step"; }
        if (iconEl) { iconEl.textContent = s.id.split("-")[1].charAt(0).toUpperCase(); }
    });

    steps.forEach((s, idx) => {
        setTimeout(() => {
            const el = document.getElementById(s.id);
            const iconEl = document.getElementById(s.icon);
            if (el) {
                el.className = idx === steps.length - 1 ? "timeline-step completed" : "timeline-step active";
            }
            if (iconEl) {
                iconEl.textContent = "✓";
            }
            if (percentLabel) {
                percentLabel.textContent = s.pct;
            }

            if (idx === steps.length - 1) {
                setTimeout(() => {
                    openMergedClaimReview("CLM-2026-90124");
                }, 600);
            }
        }, s.delay);
    });
}

let resolvedFixesCount = 0;

function switchReviewSubTab(tabName) {
    ['summary', 'issues', 'documents'].forEach(t => {
        const btn = document.getElementById(`tab-btn-${t}`);
        const content = document.getElementById(`subtab-${t}`);
        if (btn) btn.classList.remove('active');
        if (content) content.style.display = 'none';
    });

    const activeBtn = document.getElementById(`tab-btn-${tabName}`);
    const activeContent = document.getElementById(`subtab-${tabName}`);
    if (activeBtn) activeBtn.classList.add('active');
    if (activeContent) activeContent.style.display = 'block';
}

function acceptFix(issueId) {
    if (issueId === 'issue-1') {
        const btn = document.getElementById('btn-accept-1');
        const card = document.getElementById('card-issue-1');
        if (btn) {
            btn.textContent = '✓ Fix Accepted (Mod -25 Appended)';
            btn.disabled = true;
            btn.style.background = '#10b981';
            btn.style.color = '#000000';
        }
        if (card) { card.style.borderColor = '#10b981'; }
    } else if (issueId === 'issue-2') {
        const btn = document.getElementById('btn-accept-2');
        const card = document.getElementById('card-issue-2');
        if (btn) {
            btn.textContent = '✓ Fix Accepted (Package Bundled)';
            btn.disabled = true;
            btn.style.background = '#10b981';
            btn.style.color = '#000000';
        }
        if (card) { card.style.borderColor = '#10b981'; }
    }
    resolvedFixesCount++;
    checkAllFixesResolved();
}

function rejectFix(issueId) {
    alert(`Fix for ${issueId} rejected by reviewer.`);
}

function checkAllFixesResolved() {
    const bottomBadge = document.getElementById('pr-bottom-status-badge');
    const mainBtn = document.getElementById('btn-submit-main');
    const topBadge = document.getElementById('pr-status-badge');
    const topScore = document.getElementById('pr-risk-score');
    const decisionTitle = document.getElementById('summary-decision-title');
    const decisionBadge = document.getElementById('summary-decision-badge');

    if (resolvedFixesCount >= 2) {
        if (bottomBadge) { bottomBadge.className = 'badge badge-success'; bottomBadge.textContent = 'All Issues Resolved (100% Scrubber Compliant)'; }
        if (mainBtn) {
            mainBtn.textContent = 'Submit Claim →';
            mainBtn.style.background = 'linear-gradient(135deg, #10b981, #00f2fe)';
            mainBtn.style.color = '#000000';
        }
        if (topBadge) { topBadge.className = 'badge badge-success'; topBadge.textContent = 'READY TO SUBMIT'; }
        if (topScore) { topScore.style.color = '#10b981'; topScore.textContent = '0% LOW RISK'; }
        if (decisionTitle) { decisionTitle.textContent = 'Ready to Submit — Passed AI Scrubber'; }
        if (decisionBadge) { decisionBadge.className = 'badge badge-success'; decisionBadge.textContent = 'Compliant'; }
    }
}

function highlightOCRText(findingId) {
    switchReviewSubTab('documents');
    const el1 = document.getElementById('ocr-finding-1');
    const el2 = document.getElementById('ocr-finding-2');
    if (el1) el1.classList.remove('pulse-active');
    if (el2) el2.classList.remove('pulse-active');

    const target = document.getElementById(`ocr-${findingId}`);
    if (target) {
        target.classList.add('pulse-active');
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function submitClaimFinal() {
    alert('Submitted claim batch #CLM-2026-90124 directly to Star Health TPA Portal!');
}

function inviteUserModal() {
    const email = prompt("Enter email address of team member to invite to hospital workspace:");
    if (email && email.trim()) {
        alert(`Invitation sent to ${email} with role 'Billing Clerk'.`);
    }
}

/* Keyboard Shortcut: Ctrl + K or Cmd + K */
document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        openCmdPalette();
    }
    if (e.key === "Escape") {
        closeCmdPalette();
    }
});

function openCmdPalette() {
    const backdrop = document.getElementById("cmd-modal-backdrop");
    const input = document.getElementById("cmd-search-field");
    if (backdrop) backdrop.classList.add("open");
    if (input) {
        input.value = "";
        input.focus();
        filterCmdSearch("");
    }
}

function closeCmdPalette() {
    const backdrop = document.getElementById("cmd-modal-backdrop");
    if (backdrop) backdrop.classList.remove("open");
}

/* Enterprise Search Index */
const enterpriseSearchIndex = [
    { category: "CLAIMS", title: "#CLM-2026-90124 — Sunita Verma (₹1,29,000.00)", sub: "Star Health Insurance • In Review", tab: "claim-review" },
    { category: "CLAIMS", title: "#CLM-90128 — Amitabh Sharma (₹34,500.00)", sub: "HDFC ERGO Health • Missing Pre-Auth", tab: "claims" },
    { category: "PATIENTS", title: "Sunita Verma (UHID-90214)", sub: "DOB: 1985-04-12 • Active Coverage: Star Health", tab: "claim-review" },
    { category: "APPEALS", title: "Case #APP-2026-04 — ICICI Lombard Rejection", sub: "Claim #CLM-77019 (₹18,500.00 At Risk)", tab: "appeals" }
];

function filterCmdSearch(query) {
    const container = document.getElementById("cmd-results-container");
    if (!container) return;

    const q = query.trim().toLowerCase();
    const filtered = enterpriseSearchIndex.filter(item => 
        item.title.toLowerCase().includes(q) ||
        item.sub.toLowerCase().includes(q) ||
        item.category.toLowerCase().includes(q)
    );

    if (filtered.length === 0) {
        container.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-muted);">No matching claims found.</div>`;
        return;
    }

    let html = "";
    filtered.forEach(item => {
        html += `
            <div class="cmd-result-item" onclick="selectCmdResult('${item.tab}')">
                <div>
                    <div style="font-weight: 600; color: #fff;">${item.title}</div>
                    <div class="text-sub" style="font-size: 0.78rem;">${item.sub}</div>
                </div>
                <span class="kbd-badge" style="font-size: 0.7rem;">Open →</span>
            </div>
        `;
    });

    container.innerHTML = html;
}

function selectCmdResult(targetTab) {
    closeCmdPalette();
    if (targetTab === "claim-review") {
        openMergedClaimReview("CLM-2026-90124");
    } else {
        window.location.hash = targetTab;
        const navItems = document.querySelectorAll(".nav-item");
        const views = document.querySelectorAll(".dashboard-view");

        navItems.forEach(item => {
            if (item.dataset.tab === targetTab) item.classList.add("active");
            else item.classList.remove("active");
        });

        views.forEach(view => {
            if (view.id === `view-${targetTab}`) view.classList.add("active");
            else view.classList.remove("active");
        });
    }
}
