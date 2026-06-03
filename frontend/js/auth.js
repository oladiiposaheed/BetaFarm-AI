// Auth.js - Authentication helpers

const API_BASE_URL = '/api';

// Check if user is authenticated
function isAuthenticated() {
    const token = localStorage.getItem('access_token');
    return token !== null;
}

// Get auth header for API requests
function getAuthHeader() {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Logout user
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('userName');
    localStorage.removeItem('userPhone');
    window.location.href = '/';
}

// Redirect to login if not authenticated
function requireAuth() {
    if (!isAuthenticated() && !window.location.pathname.includes('index.html') && !window.location.pathname.includes('otp.html')) {
        window.location.href = '/';
    }
}

// Get current user name
function getUserName() {
    return localStorage.getItem('userName') || 'Farmer';
}

// Refresh token (call when API returns 401)
async function refreshToken() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return false;
    
    try {
        const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh })
        });
        
        const data = await response.json();
        if (response.ok) {
            localStorage.setItem('access_token', data.access);
            return true;
        }
        return false;
    } catch (error) {
        return false;
    }
}

// Make authenticated API request with auto-refresh
async function apiRequest(url, options = {}) {
    let token = localStorage.getItem('access_token');
    
    const makeRequest = async (retry = false) => {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };
        
        const response = await fetch(url, { ...options, headers });
        
        if (response.status === 401 && !retry) {
            const refreshed = await refreshToken();
            if (refreshed) {
                token = localStorage.getItem('access_token');
                return makeRequest(true);
            } else {
                logout();
                throw new Error('Session expired');
            }
        }
        
        return response;
    };
    
    return makeRequest();
}

// Run on every page
document.addEventListener('DOMContentLoaded', () => {
    requireAuth();
    
    // Set user name in UI if element exists
    const userNameSpan = document.getElementById('userName');
    if (userNameSpan) {
        userNameSpan.textContent = getUserName();
    }
    
    // Setup logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});