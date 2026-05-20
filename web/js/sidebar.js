/* Tạo sidebar SVG icons cho tất cả trang - có phân quyền role */
function renderSidebar(activePage) {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const isAdmin = user.role === 'admin';

    const pages = [
        { href: '/dashboard', label: 'Tổng quan', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>' },
        { href: '/students-page', label: 'Sinh viên', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>' },
        { href: '/classes-page', label: 'Lớp học', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>' },
        { href: '/attendance-page', label: 'Điểm danh', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' }
    ];

    // Admin: thêm mục Quản lý GV
    if (isAdmin) {
        pages.push({
            href: '/lecturers-page', label: 'Quản lý GV', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
        });
    }

    const navHtml = pages.map(p =>
        `<a href="${p.href}" class="nav-link${p.href === activePage ? ' active' : ''}">${p.svg}${p.label}</a>`
    ).join('');

    const roleName = isAdmin ? 'Quản trị viên' : 'Giảng viên';
    const displayName = user.full_name || 'Giảng viên';

    const isLightTheme = localStorage.getItem('theme') === 'light';
    const themeIcon = isLightTheme 
        ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>` // Moon icon
        : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>`; // Sun icon

    return `<aside class="sidebar">
        <div class="brand">
            <div class="brand-icon"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 1.66 2.69 3 6 3s6-1.34 6-3v-5"/></svg></div>
            <h2>AI Attendance</h2>
            <button class="theme-toggle" onclick="toggleTheme()" style="background:none;border:none;color:var(--text-dim);cursor:pointer;margin-left:auto;display:flex;align-items:center;justify-content:center;padding:6px;border-radius:8px;transition:var(--transition)" title="Chuyển chế độ sáng/tối">
                ${themeIcon}
            </button>
        </div>
        <nav>${navHtml}</nav>
        <div class="sidebar-footer">
            <a href="/profile-page" class="user-card" style="text-decoration:none;color:inherit;cursor:pointer">
                <div class="avatar"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>
                <div><div class="name" id="userName">${displayName}</div><div class="role">${roleName}</div></div>
            </a>
            <button class="btn btn-ghost btn-sm" onclick="logout()" style="width:100%;justify-content:center">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                Đăng xuất
            </button>
        </div>
    </aside>`;
}

function toggleTheme() {
    const isLight = document.body.classList.toggle('light-theme');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    // Refresh sidebar to update icon
    const sb = document.getElementById('sidebar-root');
    if (sb) sb.innerHTML = renderSidebar(location.pathname);
}

// Apply theme instantly on load before DOMContentLoaded to prevent flicker
(function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
    }
})();

/* Auto-insert sidebar */
document.addEventListener('DOMContentLoaded', () => {
    const sb = document.getElementById('sidebar-root');
    if (sb) sb.innerHTML = renderSidebar(location.pathname);
});
