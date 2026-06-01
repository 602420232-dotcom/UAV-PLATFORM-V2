function createToast(msg) {
  const t = document.createElement('div');
  t.textContent = msg;
  Object.assign(t.style, {
    position: 'fixed', bottom: '20px', right: '20px',
    background: '#333', color: '#fff', padding: '12px 20px',
    borderRadius: '8px', zIndex: 9999, fontSize: '14px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.3)', maxWidth: '400px',
    wordBreak: 'break-all'
  });
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

let chart;
let currentPage = 'monitor';

async function testGithub() {
  const el = document.getElementById('githubResult');
  const btn = document.getElementById('githubBtn');
  el.textContent = '\u23f3 \u6d4b\u8bd5\u4e2d...'; btn.disabled = true;
  try {
    const r = await fetch('/api/test-github');
    const d = await r.json();
    el.textContent = d.msg;
    el.style.color = d.success ? 'var(--accent)' : 'var(--danger)';
  } catch(e) {
    el.textContent = '\u274c \u8bf7\u6c42\u5931\u8d25'; el.style.color = 'var(--danger)';
  }
  btn.disabled = false;
}

async function runSpeedTest() {
  const el = document.getElementById('speedResult');
  const btn = document.getElementById('speedBtn');
  el.textContent = '\u23f3 \u6d4b\u901f\u4e2d\uff08\u4e0b\u8f7d 1MB\uff09\u2026'; btn.disabled = true;
  try {
    const r = await fetch('/api/speedtest');
    const d = await r.json();
    el.textContent = d.msg;
    el.style.color = d.success ? 'var(--accent)' : 'var(--danger)';
  } catch(e) {
    el.textContent = '\u274c \u8bf7\u6c42\u5931\u8d25'; el.style.color = 'var(--danger)';
  }
  btn.disabled = false;
}

function toggleTheme() {
  const body = document.body;
  const btn = document.getElementById('themeBtn');
  body.classList.toggle('light');
  if (body.classList.contains('light')) { btn.innerText = '\u2600\ufe0f'; localStorage.setItem('theme', 'light'); }
  else { btn.innerText = '\ud83c\udf19'; localStorage.setItem('theme', 'dark'); }
}

window.onload = () => {
  if (localStorage.getItem('theme') === 'light') { document.body.classList.add('light'); document.getElementById('themeBtn').innerText = '\u2600\ufe0f'; }
  initChart(); updateClock(); loadStatus(); loadProcs(); loadDocker(); loadHistory(); loadBashrc(); checkOC();
};

function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + pageId).classList.add('active');
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    const keywords = { monitor: '\u76d1\u63a7\u9762\u677f', nettest: '\u7f51\u7edc\u6d4b\u8bd5', bashrc: 'Bashrc', tools: '\u5de5\u5177\u805a\u5408' };
    if(item.textContent.includes(keywords[pageId])) item.classList.add('active');
  });
  currentPage = pageId;
  if (pageId === 'nettest') { loadNetTest(); testGoogle(); }
}

function updateClock() {
  const now = new Date();
  const options = { hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', weekday: 'long' };
  document.getElementById('clock').innerText = now.toLocaleString('zh-CN', options);
}

function initChart() {
  const ctx = document.getElementById('myChart');
  if (!ctx || typeof Chart === 'undefined') { if(ctx) ctx.parentNode.innerHTML = '<p style="color:#888">Chart.js \u52a0\u8f7d\u5931\u8d25</p>'; return; }
  chart = new Chart(ctx.getContext('2d'), {
    type: 'line', data: { labels: [], datasets: [
      { label: 'CPU Load', data: [], borderColor: '#66bb6a', fill: false, tension: 0.1 },
      { label: 'Memory %', data: [], borderColor: '#42a5f5', fill: false, tension: 0.1 },
      { label: 'GPU %', data: [], borderColor: '#ffca28', fill: false, tension: 0.1 }
    ]},
    options: { responsive: true, scales: { y: { beginAtZero: true, max: 100 } } }
  });
}

function updateChart(history) {
  if (!chart) return;
  chart.data.labels = history.time;
  chart.data.datasets[0].data = history.cpu;
  chart.data.datasets[1].data = history.mem;
  chart.data.datasets[2].data = history.gpu;
  chart.update('none');
}

async function loadStatus() {
  const res = await fetch('/api/status');
  const d = await res.json();
  document.getElementById('cpu1').innerText = d.cpu.load1;
  document.getElementById('memP').innerText = d.mem.usage + '%';
  document.getElementById('diskU').innerText = d.disk.usage + '%';
  document.getElementById('rxS').innerText = d.net.rxSpeed + ' KB/s';
  document.getElementById('txS').innerText = d.net.txSpeed + ' KB/s';
  document.getElementById('totalRx').innerText = d.net.totalRxGB + ' GB';
  document.getElementById('totalTx').innerText = d.net.totalTxGB + ' GB';
  document.getElementById('gpuU').innerText = typeof d.gpu === 'number' ? d.gpu + '%' : 'N/A';
  document.getElementById('ipAddr').innerText = d.ip.address;
  document.getElementById('ipGW').innerText = d.ip.gateway;
  document.getElementById('httpProxy').innerText = d.ip.proxy;
  document.getElementById('httpsProxy').innerText = d.ip.httpsProxy;
  document.getElementById('googleTestMini').innerText = d.ip.gateway ? '\u7f51\u5173\u6b63\u5e38' : '\u26a0\ufe0f \u7f51\u5173\u5f02\u5e38';
}

async function loadProcs() {
  const res = await fetch('/api/procs');
  const data = await res.json();
  const tbody = document.querySelector('#procTable tbody');
  tbody.innerHTML = '';
  data.forEach(p => {
    if (!p.pid || p.pid === 'PID') return;
    const tr = document.createElement('tr');
    tr.innerHTML = '<td>' + p.user + '</td><td>' + p.pid + '</td><td>' + p.cpu + '</td><td>' + p.mem + '</td><td>' + p.cmd + '</td><td><button class="btn btn-danger" style="padding:2px 8px" onclick="killProc(' + p.pid + ')">Kill</button></td>';
    tbody.appendChild(tr);
  });
}

async function killProc(pid) {
  if (!confirm('\u786e\u5b9a\u8981\u7ec8\u6b62\u8fdb\u7a0b ' + pid + ' \u5417\uff1f')) return;
  const res = await fetch('/api/action/kill-proc', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({pid}) });
  createToast((await res.json()).msg || '操作完成');
  loadProcs();
}

async function loadDocker() {
  const [listRes, statsRes] = await Promise.all([
    fetch('/api/docker'),
    fetch('/api/docker/stats')
  ]);
  let data = await listRes.json();
  const stats = await statsRes.json();
  const div = document.getElementById('dockerList');
  data = data.filter(function(c) { return c.Image.indexOf('kindest') === -1 && c.Image.indexOf('cloud-provider') === -1 && c.Image.indexOf('registry-mirror') === -1; });
  if (!data.length) { div.innerText = 'No project containers'; return; }
  var t = document.createElement('table');
  var hdr = t.insertRow();
  ['Name','Status','CPU','Mem','Ops'].forEach(function(l) { var c = hdr.insertCell(); c.textContent = l; c.style.fontWeight = 'bold'; });
  data.forEach(function(c) {
    var s = stats[c.Id] || {};
    var cpu = s.cpuPercent || '?';
    var mem = s.memMB || '?';
    var sc = c.State === 'running' ? '#4caf50' : c.State.indexOf('Up') >= 0 ? '#8bc34a' : '#f44336';
    var rc = cpu > 80 ? 'var(--danger)' : cpu > 50 ? 'var(--accent)' : 'inherit';
    var nm = c.Names.join('').replace('/','');
    var row = t.insertRow();
    row.insertCell().textContent = nm;
    var scell = row.insertCell(); scell.textContent = c.State.substring(0,12); scell.style.color = sc;
    var ccell = row.insertCell(); ccell.textContent = cpu + '%'; ccell.style.color = rc;
    row.insertCell().textContent = mem + 'MB';
    var acell = row.insertCell();
    if (c.State === 'running' || c.State.indexOf('Up') >= 0) {
      var sb = document.createElement('button'); sb.textContent = 'Stop'; sb.onclick = function() { dockerAction(c.Id,'stop'); }; acell.appendChild(sb);
      var rb = document.createElement('button'); rb.textContent = 'Restart'; rb.onclick = function() { dockerAction(c.Id,'restart'); }; acell.appendChild(rb);
    } else {
      var stb = document.createElement('button'); stb.textContent = 'Start'; stb.onclick = function() { dockerAction(c.Id,'start'); }; acell.appendChild(stb);
    }
  });
  div.innerHTML = '';
  div.appendChild(t);
}

async function dockerAction(id, action) {
  const res = await fetch('/api/docker/' + id + '/' + action, { method: 'POST' });
  const d = await res.json();
  if (d.ok) { setTimeout(loadDocker, 2000); } else { createToast('失败: ' + d.error); }
}

async function loadHistory() {
  const res = await fetch('/api/history');
  const d = await res.json();
  updateChart(d);
}

async function loadNetTest() {
  const btn = document.getElementById('retryBtn');
  btn.disabled = true; btn.innerText = '\u23f3 \u6d4b\u8bd5\u4e2d...';
  ['local', 'alidns', 'tencentdns', 'baidudns', 'googledns', 'baidu'].forEach(id => { document.getElementById('test-' + id).innerText = '\u68c0\u6d4b\u4e2d...'; });
  const res = await fetch('/api/nettest');
  const d = await res.json();
  document.getElementById('test-local').innerText = d.local;
  document.getElementById('test-alidns').innerText = d.alidns;
  document.getElementById('test-tencentdns').innerText = d.tencentdns;
  document.getElementById('test-baidudns').innerText = d.baidudns;
  document.getElementById('test-googledns').innerText = d.googledns;
  document.getElementById('test-baidu').innerText = d.baidu;
  document.getElementById('testTime').innerText = d.timestamp;
  btn.disabled = false; btn.innerText = '\ud83d\udd04 \u91cd\u65b0\u6d4b\u8bd5';
}

async function testGoogle() {
  const div = document.getElementById('googleResult');
  const btn = document.getElementById('googleBtn');
  div.innerText = '\u23f3 \u6b63\u5728\u6d4b\u8bd5 Google (Timeout 6s)...';
  btn.disabled = true;
  const res = await fetch('/api/test-google');
  const d = await res.json();
  if (d.success) { div.style.color = 'var(--accent)'; div.innerText = d.msg; }
  else { div.style.color = 'var(--danger)'; div.innerText = d.msg; }
  btn.disabled = false;
}

async function loadBashrc() {
  const res = await fetch('/api/bashrc');
  const d = await res.json();
  document.getElementById('bashrcEditor').value = d.content;
}

async function saveAndSource() {
  const content = document.getElementById('bashrcEditor').value;
  const btn = document.getElementById('saveBtn');
  btn.disabled = true;
  btn.innerText = '\ud83d\udcbe \u4fdd\u5b58\u4e2d...';
  const res = await fetch('/api/bashrc', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({content})
  });
  const d = await res.json();
  createToast(d.msg || d.error);
  btn.disabled = false;
  btn.innerText = '\ud83d\udcbe \u4fdd\u5b58';
}

async function checkOC() {
  const res = await fetch('/api/openclaw/status');
  const data = await res.json();
  const statusEl = document.getElementById('oc-status');
  statusEl.innerText = data.msg;
  statusEl.style.color = data.running ? 'green' : '#888';
}

async function startOC() {
  document.getElementById('oc-result').innerText = '\u6b63\u5728\u542f\u52a8...';
  const res = await fetch('/api/openclaw/start', { method: 'POST' });
  const data = await res.json();
  document.getElementById('oc-result').innerText = data.msg;
  setTimeout(checkOC, 3000);
}

async function stopOC() {
  document.getElementById('oc-result').innerText = '\u6b63\u5728\u505c\u6b62...';
  const res = await fetch('/api/openclaw/stop', { method: 'POST' });
  const data = await res.json();
  document.getElementById('oc-result').innerText = data.msg;
  setTimeout(checkOC, 2000);
}

async function doAction(action) {
  if (!confirm('\u786e\u5b9a\u6267\u884c\u64cd\u4f5c: ' + action + '?\n(\u6ce8\u610f\uff1a\u91cd\u542f\u64cd\u4f5c\u53ef\u80fd\u5bfc\u81f4\u8fde\u63a5\u65ad\u5f00)')) return;
  const res = await fetch('/api/action/' + action, { method: 'POST' });
  const data = await res.json();
  document.getElementById('actionResult').innerText = data.msg || data.error;
}

setInterval(updateClock, 1000);
setInterval(() => { if(currentPage === 'monitor') loadStatus(); }, 2000);
setInterval(() => { if(currentPage === 'monitor') loadProcs(); }, 5000);
setInterval(() => { if(currentPage === 'monitor') loadHistory(); }, 5000);
setInterval(() => { if(currentPage === 'monitor') loadDocker(); }, 5000);
