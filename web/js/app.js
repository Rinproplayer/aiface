/**
 * AI Face Attendance - JavaScript Chính
 * =======================================
 * Xử lý logic cho Web Dashboard:
 * - API calls, WebSocket, Toast notifications
 * - Quản lý authentication
 */

const API_BASE = '';
let wsConnection = null;

// ============================================
// AUTHENTICATION
// ============================================
function getToken() { return localStorage.getItem('token'); }
function getUser() {
    try { return JSON.parse(localStorage.getItem('user')); }
    catch { return null; }
}

function checkAuth() {
    if (!getToken()) {
        window.location.href = '/';
        return false;
    }
    return true;
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

function setupUserInfo() {
    const user = getUser();
    if (!user) return;
    const nameEl = document.getElementById('userName');
    if (nameEl) nameEl.textContent = user.full_name || user.username;
}

// ============================================
// API HELPER
// ============================================
async function apiCall(url, method = 'GET', body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) opts.body = JSON.stringify(body);
    
    const res = await fetch(API_BASE + url, opts);
    if (res.status === 401) { logout(); return null; }
    
    // Check if response is JSON
    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Lỗi server');
        return data;
    }
    
    if (!res.ok) throw new Error('Lỗi server');
    return res;
}

// ============================================
// TOAST NOTIFICATIONS
// ============================================
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
        <span class="toast-message">${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ============================================
// WEBSOCKET
// ============================================
function connectWebSocket() {
    if (wsConnection) return;
    
    const wsUrl = `ws://${window.location.host}/ws`;
    wsConnection = new WebSocket(wsUrl);

    wsConnection.onopen = () => {
        console.log('📡 WebSocket connected');
        const dot = document.getElementById('realtimeDot');
        if (dot) dot.style.background = 'var(--accent-green)';
    };

    wsConnection.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'attendance') {
            showToast(`${data.student_name} (${data.student_code}) đã điểm danh lúc ${data.time}`, 'success');
            addFeedItem(data);
            refreshDashboardStats();
        }
    };

    wsConnection.onclose = () => {
        console.log('📡 WebSocket disconnected');
        wsConnection = null;
        const dot = document.getElementById('realtimeDot');
        if (dot) dot.style.background = 'var(--accent-red)';
        // Reconnect after 3s
        setTimeout(connectWebSocket, 3000);
    };

    wsConnection.onerror = () => { wsConnection = null; };

    // Ping keep-alive
    setInterval(() => {
        if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
            wsConnection.send('ping');
        }
    }, 30000);
}

function addFeedItem(data) {
    const feed = document.getElementById('attendanceFeed');
    if (!feed) return;

    const initials = data.student_name.split(' ').map(w => w[0]).join('').slice(-2);
    const item = document.createElement('div');
    item.className = 'feed-item';
    item.innerHTML = `
        <div class="feed-avatar">${initials}</div>
        <div class="feed-info">
            <div class="feed-name">${data.student_name}</div>
            <div class="feed-detail">${data.student_code} • Độ tin cậy: ${(data.confidence * 100).toFixed(0)}%</div>
        </div>
        <span class="feed-time">${data.time}</span>
    `;

    feed.insertBefore(item, feed.firstChild);
    
    // Remove empty state
    const empty = feed.querySelector('.empty-state');
    if (empty) empty.remove();
}

async function refreshDashboardStats() {
    try {
        const stats = await apiCall('/api/dashboard/stats');
        if (!stats) return;
        const el = (id) => document.getElementById(id);
        if (el('statStudents')) el('statStudents').textContent = stats.total_students || 0;
        if (el('statClasses')) el('statClasses').textContent = stats.total_classes || 0;
        if (el('statToday')) el('statToday').textContent = stats.today_attendance || 0;
        if (el('statFaces')) el('statFaces').textContent = stats.face_registered || 0;
    } catch (e) { /* silent */ }
}

// ============================================
// MODAL HELPERS
// ============================================
function openModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// ============================================
// SIDEBAR ACTIVE STATE
// ============================================
function setActiveNav() {
    const path = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('href') === path) {
            item.classList.add('active');
        }
    });
}

// ============================================
// FORMAT HELPERS
// ============================================
function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('vi-VN');
}

function formatDateTime(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleString('vi-VN');
}

function statusBadge(status) {
    const map = {
        'present': '<span class="badge badge-success">Có mặt</span>',
        'late': '<span class="badge badge-warning">Trễ</span>',
        'absent': '<span class="badge badge-danger">Vắng</span>'
    };
    return map[status] || status;
}

// ============================================
// INIT
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname !== '/' && window.location.pathname !== '/index.html') {
        if (!checkAuth()) return;
        setupUserInfo();
        setActiveNav();
        connectWebSocket();
    }
});
