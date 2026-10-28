const API_BASE = ""; 

function getAccessToken() {
    return localStorage.getItem("access_token");
}

function setAccessToken(token) {
    localStorage.setItem("access_token", token);
}

function getRefreshToken() {
    return localStorage.getItem("refresh_token");
}

function setRefreshToken(token) {
    localStorage.setItem("refresh_token", token);
}

function getUser() {
    const userStr = localStorage.getItem("user");
    try { return userStr ? JSON.parse(userStr) : null; }
    catch { return null; }
}

function setUser(user) {
    localStorage.setItem("user", JSON.stringify(user));
}

let isRefreshing = false;
let refreshSubscribers = [];

function subscribeTokenRefresh(cb) {
    refreshSubscribers.push(cb);
}

function onRefreshed(token) {
    refreshSubscribers.forEach(cb => cb(token));
    refreshSubscribers = [];
}

async function attemptRefresh() {
    if (isRefreshing) {
        return new Promise(resolve => {
            subscribeTokenRefresh(token => {
                resolve(!!token);
            });
        });
    }
    
    isRefreshing = true;
    try {
        const payload = {};
        const rf = getRefreshToken();
        if (rf) {
            payload.refresh_token = rf;
        }
        
        const res = await fetch("/auth/refresh", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            const data = await res.json();
            setAccessToken(data.access_token);
            if (data.refresh_token) {
                setRefreshToken(data.refresh_token);
            }
            onRefreshed(data.access_token);
            isRefreshing = false;
            return true;
        }
    } catch (e) {
        console.error("Token refresh failed", e);
    }
    
    onRefreshed(null);
    isRefreshing = false;
    clearAuthStorage();
    return false;
}

// Authenticated fetch wrapper
async function authFetch(url, options = {}) {
    options.headers = options.headers || {};
    
    const token = getAccessToken();
    if (token) {
        options.headers["Authorization"] = `Bearer ${token}`;
    }
    
    // Detect if we should serialize JSON body
    if (options.body && typeof options.body === "object" && !(options.body instanceof FormData) && !(options.body instanceof Blob)) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(options.body);
    }
    
    try {
        let response = await fetch(url, options);
        
        if (response.status === 401) {
            const refreshed = await attemptRefresh();
            if (refreshed) {
                // Retry request with the new access token
                const newToken = getAccessToken();
                options.headers["Authorization"] = `Bearer ${newToken}`;
                response = await fetch(url, options);
            } else {
                // Refresh failed; clear cache and redirect to login
                logoutUser();
            }
        }
        
        return response;
    } catch (err) {
        console.error(`Fetch error on ${url}:`, err);
        throw err;
    }
}

function logoutUser() {
    clearAuthStorage();
    // HttpOnly cookie deletion
    fetch("/auth/logout", { method: "POST" }).finally(() => {
        const path = window.location.pathname;
        if (!path.endsWith("login.html") && path !== "/" && path !== "/login") {
            window.location.href = "/login";
        }
    });
}

// Simple route guard check
function checkAuth() {
    const token = getAccessToken();
    const path = window.location.pathname;
    
    const isPublicPage = path === "/" || path === "/learn" || path.startsWith("/topic/") || path === "/forgot-password" || path === "/reset-password";
    if (isPublicPage) return;
    const isAuthPage = path.endsWith("login.html") || path.endsWith("signup.html") || path === "/login" || path === "/signup";
    
    if (!token && !isAuthPage) {
        window.location.href = "/login";
    } else if (token && isAuthPage) {
        window.location.href = "/dashboard";
    }
}

function clearAuthStorage() {
    ["access_token", "refresh_token", "user"].forEach(key => localStorage.removeItem(key));
}

// Auto-run auth guard check
document.addEventListener("DOMContentLoaded", checkAuth);
