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

let refreshPromise = null;
let authGeneration = 0;

async function attemptRefresh() {
    if (refreshPromise) return refreshPromise;
    const generation = authGeneration;
    refreshPromise = (async () => {
        try {
            const payload = {};
            const token = getRefreshToken();
            if (token) payload.refresh_token = token;
            const response = await fetch('/auth/refresh', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload), signal: AbortSignal.timeout(15000),
            });
            if (generation !== authGeneration) return null;
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) { clearAuthStorage(); return false; }
                return null;
            }
            const data = await response.json();
            if (generation !== authGeneration) return null;
            if (typeof data.access_token !== 'string' || !data.access_token || data.access_token.length > 8192) return null;
            setAccessToken(data.access_token);
            if (typeof data.refresh_token === 'string' && data.refresh_token && data.refresh_token.length <= 8192) setRefreshToken(data.refresh_token);
            return true;
        } catch { return null; }
    })();
    try { return await refreshPromise; }
    finally { refreshPromise = null; }
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
            } else if (refreshed === false) {
                // Refresh failed; clear cache and redirect to login
                logoutUser();
            } else {
                const error = new Error('Your session could not be refreshed. Check your connection and retry; your sign-in has been preserved.');
                error.code = 'session_unavailable';
                throw error;
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
    fetch('/auth/logout', { method: 'POST', signal: AbortSignal.timeout(10000), keepalive: true }).catch(() => {});
    const path = window.location.pathname;
    if (!path.endsWith('login.html') && path !== '/' && path !== '/login') window.location.href = '/login';
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
    authGeneration += 1;
    ["access_token", "refresh_token", "user"].forEach(key => localStorage.removeItem(key));
}

// Auto-run auth guard check
document.addEventListener("DOMContentLoaded", checkAuth);
