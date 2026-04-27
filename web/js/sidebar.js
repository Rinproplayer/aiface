/* Tạo sidebar SVG icons cho tất cả trang */
function renderSidebar(activePage) {
    const pages = [
        { href: '/dashboard', label: 'Tổng quan', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>' },
        { href: '/students-page', label: 'Sinh viên', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>' },
        { href: '/classes-page', label: 'Lớp học', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>' },
        { href: '/attendance-page', label: 'Điểm danh', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' }
    ];
    const navHtml = pages.map(p =>
        `<a href="${p.href}" class="nav-link${p.href === activePage ? ' active' : ''}">${p.svg}${p.label}</a>`
    ).join('');

    return `<aside class="sidebar">
        <div class="brand">
            <div class="brand-icon"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 1.66 2.69 3 6 3s6-1.34 6-3v-5"/></svg></div>
            <h2>AI Attendance</h2>
        </div>
        <nav>${navHtml}</nav>
        <div class="sidebar-footer">
            <div class="user-card">
                <div class="avatar"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>
                <div><div class="name" id="userName">Giảng viên</div><div class="role">Quản trị viên</div></div>
            </div>
            <button class="btn btn-ghost btn-sm" onclick="logout()" style="width:100%;justify-content:center">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                Đăng xuất
            </button>
        </div>
    </aside>`;
}

/* Auto-insert sidebar */
document.addEventListener('DOMContentLoaded', () => {
    const sb = document.getElementById('sidebar-root');
    if (sb) sb.innerHTML = renderSidebar(location.pathname);
});
