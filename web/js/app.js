const API='';let ws=null;
function getToken(){return localStorage.getItem('token')}
function getUser(){try{return JSON.parse(localStorage.getItem('user'))}catch{return null}}
function checkAuth(){if(!getToken()){window.location.href='/';return false}return true}
function logout(){localStorage.clear();window.location.href='/'}
function setupUser(){const u=getUser();if(u){const el=document.getElementById('userName');if(el)el.textContent=u.full_name||u.username}}

async function apiCall(url,method='GET',body=null){
    const o={method,headers:{'Content-Type':'application/json'}};
    if(body)o.body=JSON.stringify(body);
    const r=await fetch(API+url,o);
    if(r.status===401){logout();return null}
    const ct=r.headers.get('content-type');
    if(ct&&ct.includes('application/json')){const d=await r.json();if(!r.ok)throw new Error(d.detail||'Lỗi');return d}
    if(!r.ok)throw new Error('Lỗi');return r;
}

function showToast(msg,type='info'){
    let c=document.querySelector('.toasts');
    if(!c){c=document.createElement('div');c.className='toasts';document.body.appendChild(c)}
    const t=document.createElement('div');t.className='toast '+type;
    const icons={success:'✅',error:'❌',warning:'⚠️',info:'ℹ️'};
    t.innerHTML=`<span>${icons[type]||'ℹ️'}</span><span class="t-msg">${msg}</span>`;
    c.appendChild(t);
    setTimeout(()=>{t.style.opacity='0';t.style.transform='translateX(80px)';setTimeout(()=>t.remove(),300)},4000);
}

function connectWS(){
    if(ws)return;
    ws=new WebSocket(`ws://${location.host}/ws`);
    ws.onopen=()=>{const d=document.getElementById('dot');if(d)d.style.background='var(--green)'};
    ws.onmessage=(e)=>{
        const d=JSON.parse(e.data);
        if(d.type==='attendance'){showToast(`${d.student_name} (${d.student_code}) đã điểm danh lúc ${d.time}`,'success');addFeed(d);refreshStats()}
    };
    ws.onclose=()=>{ws=null;const d=document.getElementById('dot');if(d)d.style.background='var(--red)';setTimeout(connectWS,3000)};
    ws.onerror=()=>{ws=null};
    setInterval(()=>{if(ws&&ws.readyState===1)ws.send('ping')},30000);
}

function addFeed(d){
    const f=document.getElementById('feed');if(!f)return;
    const ini=d.student_name.split(' ').map(w=>w[0]).join('').slice(-2);
    const el=document.createElement('div');el.className='feed-item';
    el.innerHTML=`<div class="feed-av">${ini}</div><div class="feed-info"><div class="feed-name">${d.student_name}</div><div class="feed-sub">${d.student_code} • ${(d.confidence*100).toFixed(0)}%</div></div><span class="feed-time">${d.time}</span>`;
    f.insertBefore(el,f.firstChild);
    const empty=f.querySelector('.empty');if(empty)empty.remove();
}

async function refreshStats(){
    try{
        const s=await apiCall('/api/dashboard/stats');if(!s)return;
        const el=id=>document.getElementById(id);
        if(el('sStudents'))el('sStudents').textContent=s.total_students||0;
        if(el('sClasses'))el('sClasses').textContent=s.total_classes||0;
        if(el('sToday'))el('sToday').textContent=s.today_attendance||0;
        if(el('sFaces'))el('sFaces').textContent=s.face_registered||0;
    }catch(e){}
}

function openModal(id){document.getElementById(id).classList.add('open')}
function closeModal(id){document.getElementById(id).classList.remove('open')}
function fmtDate(s){if(!s)return'';return new Date(s).toLocaleDateString('vi-VN')}
function fmtDateTime(s){if(!s)return'';return new Date(s).toLocaleString('vi-VN')}
function statusBadge(s){const m={present:'<span class="badge badge-ok">Có mặt</span>',late:'<span class="badge badge-warn">Trễ</span>',absent:'<span class="badge badge-err">Vắng</span>'};return m[s]||s}

document.addEventListener('DOMContentLoaded',()=>{
    if(location.pathname!=='/'&&location.pathname!=='/index.html'){
        if(!checkAuth())return;setupUser();
        document.querySelectorAll('.nav-link').forEach(n=>{n.classList.toggle('active',n.getAttribute('href')===location.pathname)});
        connectWS();
    }
});
