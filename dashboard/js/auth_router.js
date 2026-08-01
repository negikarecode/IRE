/**
 * Production Session Management & Route Guard for Hospital Workspace MVP
 */

async function validateSession() {
    const token = localStorage.getItem("ire_access_token") || sessionStorage.getItem("ire_access_token");
    const currentPath = window.location.pathname;

    // Allow landing page index.html without auth token
    if (currentPath.endsWith("index.html") || currentPath === "/" || currentPath.endsWith("/")) {
        return;
    }

    if (!token) {
        console.warn("[Auth Router] Unauthenticated user. Redirecting to landing page...");
        window.location.href = "index.html";
        return;
    }

    try {
        const res = await fetch("http://localhost:8000/api/v1/auth/me", {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!res.ok) {
            throw new Error("Session expired or invalid");
        }

        const user = await res.json();
        console.log("[Auth Router] Authenticated user session:", user);

        // Update UI elements with user & hospital name if present
        const userNameElem = document.querySelector(".user-name");
        const tenantTagElem = document.querySelector(".tenant-tag");
        if (userNameElem) userNameElem.textContent = user.full_name || user.email;
        if (tenantTagElem) tenantTagElem.textContent = `Facility: ${user.hospital_name}`;

    } catch (err) {
        console.warn("[Auth Router] Invalid session. Cleaning storage & redirecting:", err.message);
        localStorage.removeItem("ire_access_token");
        sessionStorage.removeItem("ire_access_token");
        window.location.href = "index.html";
    }
}

function logoutUser() {
    const token = localStorage.getItem("ire_access_token") || sessionStorage.getItem("ire_access_token");
    if (token) {
        fetch("http://localhost:8000/api/v1/auth/logout", {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        }).catch(() => {});
    }
    localStorage.removeItem("ire_access_token");
    sessionStorage.removeItem("ire_access_token");
    window.location.href = "index.html";
}

document.addEventListener("DOMContentLoaded", () => {
    // Hide platform console switch buttons
    document.querySelectorAll(".app-switch-btn").forEach(btn => btn.style.display = "none");
    validateSession();
});
