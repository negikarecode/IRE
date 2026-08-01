document.addEventListener("DOMContentLoaded", () => {
    const navItems = document.querySelectorAll(".nav-item");
    const views = document.querySelectorAll(".dashboard-view");
    const pageTitle = document.getElementById("page-title");
    const tenantSelect = document.getElementById("tenant-select");
    const tenantTag = document.getElementById("current-tenant-tag");

    const tabTitles = {
        "hospitals": "Hospital Facilities Dashboard",
        "patients": "Patient Demographic Index",
        "claims": "Operations Claims Pipeline",
        "ai-engine": "AI Gateway & Agent Orchestration",
        "analytics": "Platform Performance Analytics",
        "admin": "Admin Panel & RBAC Controls",
        "logs": "Cryptographic Audit Ledger",
        "notifications": "Real-Time Event Notifications",
        "reports": "Scheduled Enterprise Reports",
        "settings": "User & Account Settings"
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
    }

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.dataset.tab;
            window.location.hash = tabId;
            switchTab(tabId);
        });
    });

    const initialHash = window.location.hash.replace("#", "") || "hospitals";
    switchTab(initialHash);

    if (tenantSelect) {
        tenantSelect.addEventListener("change", () => {
            const selectedText = tenantSelect.options[tenantSelect.selectedIndex].text;
            if (tenantTag) {
                tenantTag.textContent = `Tenant: ${selectedText}`;
            }
        });
    }
});
