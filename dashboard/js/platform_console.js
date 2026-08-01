document.addEventListener("DOMContentLoaded", () => {
    const navItems = document.querySelectorAll(".nav-item");
    const views = document.querySelectorAll(".dashboard-view");
    const pageTitle = document.getElementById("page-title");
    const tenantFilter = document.getElementById("console-tenant-filter");

    const tabTitles = {
        "hospitals-management": "Hospital Management (Multi-Tenant)",
        "tenant-management": "Tenant Management & Provisioning",
        "ai-gateway": "Multi-Provider AI Gateway",
        "provider-health": "LLM Provider Health & Latency Probes",
        "llm-costs": "LLM Costs & Token Consumption Analytics",
        "ocr-usage": "Document OCR Extraction Usage & Metrics",
        "platform-analytics": "Platform Analytics & Event Streams",
        "infrastructure-monitoring": "Infrastructure Microservice Monitoring",
        "audit-ledger": "Cryptographic SHA-256 Audit Ledger",
        "subscriptions": "Enterprise Subscriptions & ARR Tracking",
        "customer-support": "Customer Support & Incident Escalations",
        "billing": "Enterprise Billing & Overages",
        "developer-tools": "Developer Tools & Founder A SDK Registry"
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

    const initialHash = window.location.hash.replace("#", "") || "hospitals-management";
    switchTab(initialHash);

    if (tenantFilter) {
        tenantFilter.addEventListener("change", () => {
            const selectedTenant = tenantFilter.options[tenantFilter.selectedIndex].text;
            console.log(`[IRE Platform Console] Filtered view to: ${selectedTenant}`);
        });
    }
});
