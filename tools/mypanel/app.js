const express = require('express');
const os = require('os');
const disk = require('diskusage');
const fs = require('fs');
const { execSync, spawn } = require('child_process'); // 引入 spawn 用于后台启动
const Docker = require('dockerode');

const app = express();
const port = 5577;

// --- 配置 ---
const AUTH_USER = process.env.MONITOR_USER || 'admin';
const AUTH_PASS = process.env.MONITOR_PASS || 'admin123';
const TRAFFIC_FILE = './traffic.json';
const BASHRC_PATH = os.homedir() + '/.bashrc';

// --- 中间件 ---
app.use(express.static(__dirname));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Disable caching for development
app.use((req, res, next) => {
  res.set('Cache-Control', 'no-store, no-cache, must-revalidate');
  next();
});

// --- Docker 初始化 ---
let docker = null;
let isDockerAvailable = false;
try {
  docker = new Docker({ socketPath: '/var/run/docker.sock' });
  docker.info((err, info) => {
    if (err) { console.warn('⚠️ Docker 已安装但无法连接 (可能未启动):', err.message); isDockerAvailable = false; } 
    else { console.log('✅ Docker 连接成功'); isDockerAvailable = true; }
  });
} catch (e) { console.warn('⚠️ Docker 模块加载失败'); }

// --- 流量与历史数据 ---
let traffic = loadTraffic();
let lastRx = 0n, lastTx = 0n, netRxSpeed = 0, netTxSpeed = 0;
let historyData = { cpu: [], mem: [], netRx: [], gpu: [], time: [] };
const MAX_HISTORY = 60;

function loadTraffic() {
  try { return fs.existsSync(TRAFFIC_FILE) ? JSON.parse(fs.readFileSync(TRAFFIC_FILE, 'utf8')) : { totalRx: 0, totalTx: 0 }; } catch (e) { return { totalRx: 0, totalTx: 0 }; }
}
function saveTraffic(rx, tx) { traffic = { totalRx: rx, totalTx: tx }; fs.writeFileSync(TRAFFIC_FILE, JSON.stringify(traffic, null, 2)); }

// --- 系统信息获取 ---
async function getStatus() {
  const cpu = os.loadavg();
  const totalMem = os.totalmem(), freeMem = os.freemem();
  const memUsage = ((totalMem - freeMem) / totalMem * 100).toFixed(1);
  let diskInfo = { usage: 0, total: 0, free: 0 };
  
  try { 
    const d = await disk.check('/'); 
    diskInfo.total = (d.total / 1e9).toFixed(1); 
    diskInfo.free = (d.free / 1e9).toFixed(1); 
    diskInfo.usage = (((d.total - d.free) / d.total) * 100).toFixed(1); 
  } catch (e) {}

  // GPU 监控
  let gpuUsage = 'N/A';
  try {
    const cmd = 'which nvidia-smi > /dev/null 2>&1 && nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits || echo "N/A"';
    const gpuOut = execSync(cmd, { timeout: 1500 }).toString().trim();
    if (gpuOut !== 'N/A' && !isNaN(parseInt(gpuOut))) gpuUsage = parseInt(gpuOut);
  } catch (e) {}

  // IP、网关与代理信息
  let ipInfo = { address: 'N/A', gateway: 'N/A', proxy: '未设置', httpsProxy: '未设置' };
  try {
    const route = execSync('ip route | grep default').toString().trim();
    const match = route.match(/via\s+([\d.]+)/);
    if (match) ipInfo.gateway = match[1];
    
    const addr = execSync("ip addr show eth0 | grep 'inet ' | awk '{print $2}'").toString().trim();
    if (addr) ipInfo.address = addr;

    // 检测代理端口
    if (ipInfo.gateway) {
      try {
        execSync(`nc -z -w1 ${ipInfo.gateway} 7890 2>/dev/null`, { timeout: 1500 });
        ipInfo.proxy = `http://${ipInfo.gateway}:7890 (运行中)`;
        ipInfo.httpsProxy = `http://${ipInfo.gateway}:7890 (运行中)`;
      } catch (proxyErr) {
        ipInfo.proxy = `http://${ipInfo.gateway}:7890 (未运行)`;
        ipInfo.httpsProxy = `http://${ipInfo.gateway}:7890 (未运行)`;
      }
    }
  } catch (e) {}

  // 更新历史数据
  const now = new Date().toLocaleTimeString('zh-CN', { hour12: false });
  historyData.cpu.push(parseFloat(cpu[0]));
  historyData.mem.push(parseFloat(memUsage));
  historyData.gpu.push(typeof gpuUsage === 'number' ? gpuUsage : 0);
  historyData.time.push(now);
  if (historyData.cpu.length > MAX_HISTORY) { 
    historyData.cpu.shift(); historyData.mem.shift(); historyData.gpu.shift(); historyData.time.shift(); 
  }

  return {
    cpu: { load1: cpu[0].toFixed(2) },
    mem: { usage: memUsage, total: (totalMem / 1e9).toFixed(1), free: (freeMem / 1e9).toFixed(1) },
    disk: diskInfo,
    net: { 
      rxSpeed: netRxSpeed, txSpeed: netTxSpeed, 
      totalRxGB: (traffic.totalRx / 1e9).toFixed(2), 
      totalTxGB: (traffic.totalTx / 1e9).toFixed(2) 
    },
    gpu: gpuUsage,
    ip: ipInfo
  };
}

// 流量统计
setInterval(() => {
  try {
    const data = fs.readFileSync('/proc/net/dev', 'utf8');
    for (const line of data.split('\n')) {
      if (line.includes('eth0')) {
        const p = line.trim().split(/\s+/);
        const rx = BigInt(p[1]), tx = BigInt(p[9]);
        
        if (lastRx === 0n) { lastRx = rx; lastTx = tx; return; }
        if (rx < lastRx || tx < lastTx) { 
            lastRx = rx; lastTx = tx; 
            return; 
        }
        
        const r = Number(rx - lastRx), t = Number(tx - lastTx);
        traffic.totalRx += r; traffic.totalTx += t; saveTraffic(traffic.totalRx, traffic.totalTx);
        netRxSpeed = (r / 1024).toFixed(2); netTxSpeed = (t / 1024).toFixed(2);
        lastRx = rx; lastTx = tx;
      }
    }
  } catch (e) {}
}, 1000);

// --- 鉴权中间件 ---
function checkAuth(req, res, next) {
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Basic ')) {
    res.setHeader('WWW-Authenticate', 'Basic realm="Login"');
    return res.status(401).send('Unauthorized');
  }
  const [user, pass] = Buffer.from(auth.split(' ')[1], 'base64').toString().split(':');
  if (user === AUTH_USER && pass === AUTH_PASS) return next();
  return res.status(401).send('Wrong Password');
}

// --- API 路由 ---

// 1. 主状态
app.get('/api/status', checkAuth, async (req, res) => res.json(await getStatus()));

// 2. 历史数据
app.get('/api/history', checkAuth, (req, res) => res.json(historyData));

// 3. 进程列表
app.get('/api/procs', checkAuth, (req, res) => {
  try {
    const out = execSync(`ps aux --sort=-%cpu | head -11 | awk '{print $1,$2,$3,$4,$11}'`).toString();
    const lines = out.trim().split('\n');
    const data = lines.map(line => {
      const parts = line.trim().split(/\s+/);
      return { user: parts[0], pid: parts[1], cpu: parts[2], mem: parts[3], cmd: parts.slice(4).join(' ') };
    });
    res.json(data);
  } catch (e) { res.json([]); }
});

// 4. Docker 容器列表
app.get('/api/docker', checkAuth, async (req, res) => {
  if (!isDockerAvailable || !docker) return res.json([]); 
  try { 
    const containers = await docker.listContainers({ all: true }); 
    res.json(containers); 
  } catch (e) { 
    res.json([]); 
  }
});

// 4b. Docker 容器资源统计（CPU/内存/网络）
app.get('/api/docker/stats', checkAuth, async (req, res) => {
  if (!isDockerAvailable || !docker) return res.json({});
  try {
    const containers = await docker.listContainers({ all: true });
    const result = {};
    await Promise.all(containers.map(async (c) => {
      try {
        const ct = docker.getContainer(c.Id);
        const stats = await ct.stats({ stream: false });
        const cpuDelta = stats.cpu_stats.cpu_usage.total_usage - stats.precpu_stats.cpu_usage.total_usage;
        const sysDelta = stats.cpu_stats.system_cpu_usage - stats.precpu_stats.system_cpu_usage;
        const rawCpu = sysDelta > 0 ? (cpuDelta / sysDelta) * stats.cpu_stats.online_cpus * 100 : 0;
        const cpuPercent = (rawCpu > 0 ? rawCpu : 0).toFixed(1);
        const memUsed = stats.memory_stats.usage - (stats.memory_stats.stats?.cache || 0);
        const memLimit = stats.memory_stats.limit;
        const memPercent = memLimit > 0 ? ((memUsed / memLimit) * 100).toFixed(1) : '0.0';
        const memMB = (memUsed / 1024 / 1024).toFixed(0);
        const netRx = stats.networks ? Object.values(stats.networks).reduce((a,b) => a + b.rx_bytes, 0) : 0;
        const netTx = stats.networks ? Object.values(stats.networks).reduce((a,b) => a + b.tx_bytes, 0) : 0;
        result[c.Id] = { cpuPercent, memPercent, memMB, netRx, netTx };
      } catch(e) {}
    }));
    res.json(result);
  } catch(e) { res.json({}); }
});

// 4c. Docker 容器操作（start/stop/restart）
app.post('/api/docker/:id/:action', checkAuth, async (req, res) => {
  if (!isDockerAvailable || !docker) return res.status(503).json({ error: 'Docker not available' });
  const { id, action } = req.params;
  try {
    const ct = docker.getContainer(id);
    if (action === 'start') await ct.start();
    else if (action === 'stop') await ct.stop();
    else if (action === 'restart') await ct.restart();
    else return res.status(400).json({ error: 'Invalid action' });
    res.json({ ok: true });
  } catch(e) { res.status(500).json({ error: e.message }); }
});

// 5. 网络测试 (Ping)
app.get('/api/nettest', checkAuth, (req, res) => {
  const result = { timestamp: new Date().toLocaleTimeString('zh-CN') };  
  try { execSync('ping -c 1 -W 1 127.0.0.1', {timeout:2000}); result.local = '✅ 正常'; } catch { result.local = '❌ 异常'; }
  try { execSync('ping -c 1 -W 1 223.5.5.5', {timeout:2000}); result.alidns = '✅ 正常'; } catch { result.alidns = '❌ 异常'; }
  try { execSync('ping -c 1 -W 1 119.29.29.29', {timeout:2000}); result.tencentdns = '✅ 正常'; } catch { result.tencentdns = '❌ 异常'; }
  try { execSync('ping -c 1 -W 1 180.76.76.76', {timeout:2000}); result.baidudns = '✅ 正常'; } catch { result.baidudns = '❌ 异常'; }
  try { execSync('ping -c 1 -W 1 8.8.8.8', {timeout:2000}); result.googledns = '✅ 正常'; } catch { result.googledns = '❌ 异常'; }
  try { execSync('ping -c 1 -W 1 www.baidu.com', {timeout:2000}); result.baidu = '✅ 正常'; } catch { result.baidu = '❌ 异常'; }
  res.json(result);
});

// 6. Google 专项测试 (强制走代理)
app.get('/api/test-google', checkAuth, (req, res) => {
  try {
    const gateway = execSync("ip route | awk '/default/ {print $3; exit}'").toString().trim();
    if (!gateway) return res.json({ success: false, msg: '❌ 无法获取网关 IP' });

    // 强制使用 -x 参数走代理，并使用 -I 只获取头部
    const cmd = `curl -I -m 6 -x http://${gateway}:7890 https://www.google.com 2>&1`;
    const out = execSync(cmd, { timeout: 8000 }).toString();
    
    if (out.includes('HTTP/') && !out.includes('407 Proxy Authentication Required')) {
      const statusLine = out.split('\n')[0];
      res.json({ success: true, msg: `✅ 连接成功 (via ${gateway}): ${statusLine}` });
    } else {
      res.json({ success: false, msg: `❌ 连接失败: ${out.substring(0, 150)}` });
    }
  } catch (e) {
    let errMsg = e.stderr ? e.stderr.toString() : e.message;
    if (errMsg.includes('timed out')) errMsg = '连接超时 (代理未开/端口错)';
    if (errMsg.includes('Refused')) errMsg = '连接被拒 (Clash 未开 Allow LAN)';
    res.json({ success: false, msg: '❌ ' + errMsg });
  }
});

// ── GitHub 连通性测试 ──
app.get('/api/test-github', checkAuth, (req, res) => {
  try {
    // 关键改动：加上 -s (silent) 禁止进度条，只保留 HTTP 头信息
    // 既然开了 TUN 模式，就不强制 -x 了，让系统路由自己决定（会更稳）
    const cmd = `curl -s -I -L -m 6 https://github.com 2>&1`;
    
    const out = execSync(cmd, { timeout: 8000 }).toString();

    // 调试：如果还有问题，把这一行放开看看输出了啥
    // console.log("GitHub Raw Output:", out);

    // 匹配 HTTP 状态码 (200, 301, 302 都算成功)
    if (/^HTTP\/\d[\d.]*\s+(200|301|302)/m.test(out)) {
      // 提取第一行状态
      const statusLine = out.match(/^(HTTP\/\S+\s+\d+.*)$/m);
      const msg = statusLine ? statusLine[1] : 'OK';
      res.json({ success: true, msg: `✅ GitHub 可达: ${msg}` });
    } else {
      res.json({ success: false, msg: `❌ GitHub 不可达: ${out.substring(0, 150)}` });
    }
  } catch (e) {
    let errMsg = (e.stderr || e.message || '').toString();
    if (/timed out|Timeout/i.test(errMsg)) {
      errMsg = '连接超时 (检查 Clash/TUN 模式是否开启)';
    }
    res.json({ success: false, msg: `❌ ${errMsg.substring(0, 200)}` });
  }
});

// ── 网速测试（下载 1MB 样本）──
app.get('/api/speedtest', checkAuth, (req, res) => {
  try {
    // 用 httpbin 的 stream-bytes 生成“纯数据”，避免 HTML 页面开销
    // 如果想更稳，可换成备用URL：https://speedtest.tele2.net/1MB.zip
    const url = 'https://httpbin.org/stream-bytes/1048576';
    // 使用 -s (silent) 和 --max-time，输出格式也更清晰
    const out = execSync(
      `curl -s -o /dev/null -w '__SPD__%{speed_download}__TIME__%{time_total}' --max-time 25 "${url}" 2>&1`,
      { timeout: 30000 }
    ).toString();

    const spd = out.match(/__SPD__([\d.]+)/);
    const tim = out.match(/__TIME__([\d.]+)/);
    if (!spd || !tim) return res.json({ success: false, msg: `❌ 解析失败: ${out.slice(0, 250)}` });

    const bps  = Number(spd[1]);
    const sec  = Number(tim[1]);
    const mBps = (bps / 1024 / 1024).toFixed(2);
    const kBps = (bps / 1024).toFixed(1);
    return res.json({
      success: true,
      msg: `🚀 约 ${mBps} MB/s（${kBps} KB/s），耗时 ${sec.toFixed(2)}s（下载样本 1MB）`
    });
  } catch (e) {
    const em = (e.stderr || e.message || '').toString();
    if (/timed out|Timeout/i.test(em)) return res.json({ success: false, msg: '❌ 测速超时（>25s）' });
    return res.json({ success: false, msg: `❌ ${em.slice(0, 250)}` });
  }
});

// 7. 读取 Bashrc
app.get('/api/bashrc', checkAuth, (req, res) => {
  try {
    const content = fs.readFileSync(BASHRC_PATH, 'utf8');
    res.json({ content });
  } catch (e) { res.json({ content: '# 无法读取文件', error: e.message }); }
});

// 8. 保存并重载 Bashrc
app.post('/api/bashrc', checkAuth, (req, res) => {
  const { content } = req.body;
  if (!content) return res.status(400).json({ error: '内容为空' });
  try {
    // 1. 先保存文件
    fs.writeFileSync(BASHRC_PATH, content);
    // 2. 尝试重载（主要为了检查语法是否正确，环境变量不会真的传回来）
    try {
      // 注意：这不会改变当前 Node 进程的环境变量，只对后续 spawn 的子进程有效
      execSync(`bash -c "source ${BASHRC_PATH}"`); 
      // 如果走到这，说明 source 没报错
      res.json({ msg: '✅ 保存成功！配置已写入。请重启相关服务（如 OpenClaw）以生效。' });
    } catch (sourceErr) {
      // 如果 source 失败（比如 bashrc 里有语法错误），提醒用户
      res.json({ msg: `⚠️ 保存成功，但重载配置时报错：${sourceErr.message.substring(0, 100)}` });
    }
  } catch (e) {
    // 文件写入失败
    res.status(500).json({ error: '文件写入失败: ' + e.message });
  }
});

// 9. 系统操作
app.post('/api/action/:action', checkAuth, (req, res) => {
  const { action } = req.params;
  try {
    switch (action) {
      case 'clear-traffic':
        saveTraffic(0, 0); lastRx = 0n; lastTx = 0n;
        return res.json({ msg: '✅ 流量统计已清零' });
      case 'kill-proc':
        process.kill(parseInt(req.body.pid), 'SIGTERM');
        return res.json({ msg: `✅ 进程 ${req.body.pid} 已终止` });
      case 'restart-panel':
        if (process.env.PM2_HOME || process.env.pm_id) {
            res.json({ msg: '✅ 面板正在重启...' });
            setTimeout(() => process.exit(0), 1000);
        } else {
            res.json({ msg: '⚠️ 非 PM2 环境，请手动重启' });
        }
        break;
      case 'restart-docker':
        execSync('sudo service docker restart');
        return res.json({ msg: '✅ Docker 正在重启...' });
      case 'restart-wsl':
        res.json({ msg: '⚠️ WSL 正在重启，连接即将断开...' });
        setTimeout(() => execSync('shutdown -r now'), 1000);
        break;
      default:
        return res.status(400).json({ error: '未知操作' });
    }
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
});

// --- OpenClaw 控制 API ---

// 检查状态
app.get('/api/openclaw/status', checkAuth, (req, res) => {
  try {
    execSync('pgrep -f "openclaw/dist/index.js"');
    res.json({ running: true, msg: '🦞 OpenClaw 正在运行' });
  } catch (e) {
    res.json({ running: false, msg: '⚫ OpenClaw 未运行' });
  }
});

// 启动 OpenClaw
app.post('/api/openclaw/start', checkAuth, (req, res) => {
  try {
    try {
      execSync('pgrep -f "openclaw/dist/index.js"');
      return res.json({ success: false, msg: '已经在运行了' });
    } catch (e) {}

    const logStream = fs.createWriteStream('/tmp/openclaw-gateway.log', { flags: 'a' });
    const proc = spawn('bash', ['-c', 
      'export http_proxy="http://172.27.208.1:7890"; ' +
      'export https_proxy="http://172.27.208.1:7890"; ' +
      'export NODE_TLS_REJECT_UNAUTHORIZED=0; ' +
      'openclaw gateway start'
    ], {
      detached: true,
      stdio: ['ignore', logStream, logStream]
    });
    
    proc.unref(); 
    
    res.json({ success: true, msg: '🚀 OpenClaw 正在后台启动...' });
  } catch (e) {
    res.json({ success: false, msg: '启动失败: ' + e.message });
  }
});

// 停止 OpenClaw
app.post('/api/openclaw/stop', checkAuth, (req, res) => {
  try {
    execSync('pkill -f openclaw');
    res.json({ success: true, msg: '🛑 OpenClaw 已停止' });
  } catch (e) {
    res.json({ success: false, msg: '停止失败或进程不存在' });
  }
});

// --- 前端页面 ---
app.get('/', checkAuth, (req, res) => {
  res.send(`<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WSL2 监控面板 Pro</title>
<script src="/chart.js"></script>
<style>
:root { --bg: #121212; --card: #1e1e1e; --text: #e0e0e0; --accent: #66bb6a; --warn: #ffca28; --danger: #ef5350; --link: #42a5f5; --border: #333; }
body.light { --bg: #f4f6f8; --card: #ffffff; --text: #333333; --accent: #007bff; --warn: #fd7e14; --danger: #dc3545; --link: #0056b3; --border: #dee2e6; }
body { background: var(--bg); color: var(--text); font-family: system-ui; margin:0; padding:1rem; max-width:1200px; margin:auto; transition: all 0.3s; }
.header { display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border); padding-bottom:1rem; margin-bottom:1rem; flex-wrap:wrap; }
.clock { color:var(--link); font-size:1.1rem; }
.theme-toggle { cursor:pointer; font-size:1.5rem; background:none; border:1px solid var(--border); border-radius:50%; width:40px; height:40px; display:flex; align-items:center; justify-content:center; margin-left:1rem; }
.nav { display:flex; gap:1rem; margin-bottom:1.5rem; border-bottom:2px solid var(--border); padding-bottom:0.5rem; flex-wrap:wrap; }
.nav-item { cursor:pointer; padding:0.5rem 1rem; border-radius:8px 8px 0 0; color:#aaa; text-decoration:none; }
.nav-item.active { background:var(--card); color:var(--accent); font-weight:bold; }
.page { display:none; } 
.page.active { display:block; }
.grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:1rem; }
.card { background:var(--card); border-radius:12px; padding:1.5rem; margin-bottom:1rem; box-shadow:0 4px 6px rgba(0,0,0,0.1); }
.card h3 { margin-top:0; color:var(--accent); border-bottom:1px solid var(--border); padding-bottom:0.5rem; display:flex; justify-content:space-between; align-items:center;}
.row { display:flex; justify-content:space-between; padding:0.6rem 0; border-bottom:1px dashed var(--border); font-size:14px; }
.btn { background:#555; color:white; border:none; padding:0.5rem 1rem; border-radius:6px; cursor:pointer; margin:0.2rem; font-size:14px;}
.btn-sm { padding:0.3rem 0.6rem; font-size:12px; }
.btn-link { background:transparent; color:var(--link); }
.btn-danger { background:var(--danger); }
.btn-warn { background:var(--warn); color:#000; }
table { width:100%; border-collapse:collapse; font-size:14px; }
th, td { text-align:left; padding:8px; border-bottom:1px solid var(--border); }
textarea { width:100%; height:400px; background:#111; color:#e0e0e0; border:1px solid var(--border); border-radius:8px; padding:1rem; font-family:monospace; resize:vertical; font-size:13px; }
#actionResult, #googleResult { margin-top:1rem; font-size:14px; }
.test-time { font-size:12px; color:#888; }
pre { background:#111; padding:1rem; border-radius:8px; overflow-x:auto; white-space:pre-wrap; word-break:break-all; }
</style>
</head>
<body>

<div class="header">
  <h1>🚀 WSL2 监控面板</h1>
  <div style="display:flex;align-items:center">
    <div class="clock" id="clock">加载中...</div>
    <button class="theme-toggle" onclick="toggleTheme()" id="themeBtn">🌙</button>
  </div>
</div>

<div class="nav">
  <div class="nav-item active" onclick="showPage('monitor')">📊 监控面板</div>
  <div class="nav-item" onclick="showPage('nettest')">🌐 网络测试</div>
  <div class="nav-item" onclick="showPage('bashrc')">📝 Bashrc编辑</div>
  <div class="nav-item" onclick="showPage('tools')">🧰 工具聚合</div>
</div>

<!-- 页面 1: 监控面板 -->
<div id="page-monitor" class="page active">
  <div class="grid">
    <div class="card"><h3>💻 系统负载</h3><div class="row"><span>CPU (1m)</span><span id="cpu1">-</span></div><div class="row"><span>内存</span><span id="memP">-</span></div><div class="row"><span>GPU</span><span id="gpuU" style="color:var(--warn)">-</span></div></div>
    <div class="card"><h3>💾 磁盘 & 网络</h3><div class="row"><span>磁盘</span><span id="diskU">-</span></div><div class="row"><span>下载</span><span id="rxS" style="color:var(--link)">-</span></div><div class="row"><span>上传</span><span id="txS" style="color:var(--warn)">-</span></div><div class="row"><span>累计接收</span><span id="totalRx">-</span></div><div class="row"><span>累计发送</span><span id="totalTx">-</span></div></div>
    <div class="card"><h3>🌐 IP与路由</h3><div class="row"><span>本机地址 (eth0)</span><span id="ipAddr">-</span></div><div class="row"><span>默认网关</span><span id="ipGW">-</span></div><div class="row"><span>HTTP 代理</span><span id="httpProxy" style="font-size:12px">-</span></div><div class="row"><span>HTTPS 代理</span><span id="httpsProxy" style="font-size:12px">-</span></div><div class="row"><span>Google 测试</span><span id="googleTestMini">检测中...</span></div></div>
  </div>
  <div class="card"><h3>📈 历史趋势</h3><canvas id="myChart" height="80"></canvas></div>
  <div class="card"><h3>🐳 Docker 容器 <span style="font-size:0.65em;color:#888">(点击操作)</span></h3><div id="dockerList">加载中...</div></div>
  <div class="card"><h3>⚙️ 进程管理 (Top 10)</h3><table id="procTable"><thead><tr><th>用户</th><th>PID</th><th>CPU%</th><th>内存%</th><th>命令</th><th>操作</th></tr></thead><tbody></tbody></table></div>
  <div class="card">
    <h3>🦞 OpenClaw 控制台</h3>
    <div id="oc-status" style="margin-bottom: 10px; font-weight: bold;">检测中...</div>
    <div class="controls">
      <button class="btn" onclick="startOC()">🚀 启动</button>
      <button class="btn btn-danger" onclick="stopOC()">🛑 停止</button>
      <button class="btn btn-sm btn-link" onclick="checkOC()">🔄 刷新</button>
    </div>
    <div id="oc-result" class="result-box" style="margin-top: 10px;"></div>
  </div>
  <div class="card">
    <h3>🛠️ 系统操作</h3>
    <button class="btn btn-warn" onclick="doAction('clear-traffic')">清空流量统计</button>
    <button class="btn" onclick="doAction('restart-panel')">重启面板</button>
    <button class="btn" onclick="doAction('restart-docker')">重启Docker</button>
    <button class="btn btn-danger" onclick="doAction('restart-wsl')">重启WSL</button>
    <div id="actionResult"></div>
  </div>
</div>

<!-- 页面 2: 网络测试 -->
<div id="page-nettest" class="page">
  <div class="card">
    <h3>🌐 连通性检测 <button class="btn btn-sm btn-link" onclick="loadNetTest()" id="retryBtn">🔄 重新测试</button></h3>
    <div class="test-time">上次测试: <span id="testTime">-</span></div>
    <div class="row"><span>本地回环 (127.0.0.1)</span><span id="test-local">检测中...</span></div>
    <div class="row"><span>阿里DNS (223.5.5.5)</span><span id="test-alidns">检测中...</span></div>
    <div class="row"><span>腾讯DNS (119.29.29.29)</span><span id="test-tencentdns">检测中...</span></div>
    <div class="row"><span>百度DNS (180.76.76.76)</span><span id="test-baidudns">检测中...</span></div>
    <div class="row"><span>谷歌DNS (8.8.8.8)</span><span id="test-googledns">检测中...</span></div>
    <div class="row"><span>域名解析 (www.baidu.com)</span><span id="test-baidu">检测中...</span></div>
    <hr style="border-color:var(--border); margin:1rem 0">
    <h3>🌍 Google 专项测试 <button class="btn btn-sm btn-link" onclick="testGoogle()" id="googleBtn">🔄 测试连接</button></h3>
    <div id="googleResult">点击按钮测试 https://www.google.com (Timeout 6s)</div>
    <hr style="border-color:var(--border); margin:1.2rem 0">
    <h3>🐙 GitHub 连通性 <button class="btn btn-sm btn-link" onclick="testGithub()" id="githubBtn">🔄 测试</button></h3>
    <div id="githubResult" style="margin-bottom:.8rem">点击按钮测试 github.com（HTTPS）</div>
    <h3>🚀 网速测试（1MB 样本）<button class="btn btn-sm btn-link" onclick="runSpeedTest()" id="speedBtn">🔄 测试</button></h3>
    <div id="speedResult">点击按钮开始（会短暂下载 1MB 数据）</div>
  </div>
</div>

<!-- 页面 3: Bashrc 编辑 -->
<div id="page-bashrc" class="page">
  <div class="card">
    <h3>📝 编辑 ~/.bashrc <button class="btn btn-sm btn-warn" onclick="saveAndSource()" id="saveBtn">💾 保存</button></h3>
    <p style="font-size:12px;color:#888;margin-bottom:1rem">在此编辑配置，保存后需重新进入终端或执行 source ~/.bashrc 生效。</p>
    <textarea id="bashrcEditor">加载中...</textarea>
  </div>
</div>

<!-- 页面 4: 工具聚合 -->
<div id="page-tools" class="page">
  <div class="card">
    <h3>🧰 常用链接</h3>
    <p style="margin-bottom:1rem">点击跳转常用开发资源：</p>
    <!-- 本地面板：修正端口写法 -->
    <button class="btn btn-link" onclick="window.open('http://localhost:5577','_blank')">📊 本地面板</button>
    <!-- GitHub -->
    <button class="btn btn-link" onclick="window.open('https://github.com','_blank')">GitHub</button>
    <!-- Node.js -->
    <button class="btn btn-link" onclick="window.open('https://nodejs.org','_blank')">Node.js</button>
    <!-- 百度：如果代理不支持国内，可能会慢或打不开，保留 -->
    <button class="btn btn-link" onclick="window.open('https://www.baidu.com','_blank')">百度</button>
    <!-- OpenClaw Web：直接用 18789 端口 -->
    <button class="btn btn-link" onclick="window.open('http://localhost:18789','_blank')" style="color:var(--accent)">🦞 OpenClaw Web</button>
    <!-- ★ 新增：DeepSeek 用量查询 -->
    <button class="btn btn-link" onclick="window.open('https://platform.deepseek.com/usage','_blank')" style="color:#66bb6a">📈 DeepSeek 用量</button>
  </div>
</div>

<script>
let chart;
let currentPage = 'monitor';

async function testGithub() {
  const el = document.getElementById('githubResult');
  const btn = document.getElementById('githubBtn');
  el.textContent = '⏳ 测试中...'; btn.disabled = true;
  try {
    const r = await fetch('/api/test-github');
    const d = await r.json();
    el.textContent = d.msg;
    el.style.color = d.success ? 'var(--accent)' : 'var(--danger)';
  } catch(e) {
    el.textContent = '❌ 请求失败'; el.style.color = 'var(--danger)';
  }
  btn.disabled = false;
}

async function runSpeedTest() {
  const el = document.getElementById('speedResult');
  const btn = document.getElementById('speedBtn');
  el.textContent = '⏳ 测速中（下载 1MB）…'; btn.disabled = true;
  try {
    const r = await fetch('/api/speedtest');
    const d = await r.json();
    el.textContent = d.msg;
    el.style.color = d.success ? 'var(--accent)' : 'var(--danger)';
  } catch(e) {
    el.textContent = '❌ 请求失败'; el.style.color = 'var(--danger)';
  }
  btn.disabled = false;
}

function toggleTheme() {
  const body = document.body;
  const btn = document.getElementById('themeBtn');
  body.classList.toggle('light');
  if (body.classList.contains('light')) { btn.innerText = '☀️'; localStorage.setItem('theme', 'light'); } 
  else { btn.innerText = '🌙'; localStorage.setItem('theme', 'dark'); }
}
window.onload = () => {
  if (localStorage.getItem('theme') === 'light') { document.body.classList.add('light'); document.getElementById('themeBtn').innerText = '☀️'; }
  initChart(); updateClock(); loadStatus(); loadProcs(); loadDocker(); loadHistory(); loadBashrc(); checkOC();
};

function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + pageId).classList.add('active');
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    const keywords = { monitor: '监控面板', nettest: '网络测试', bashrc: 'Bashrc', tools: '工具聚合' };
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
  if (!ctx || typeof Chart === 'undefined') { if(ctx) ctx.parentNode.innerHTML = '<p style="color:#888">Chart.js 加载失败</p>'; return; }
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
  document.getElementById('googleTestMini').innerText = d.ip.gateway ? '网关正常' : '⚠️ 网关异常';
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
  if (!confirm('确定要终止进程 ' + pid + ' 吗？')) return;
  const res = await fetch('/api/action/kill-proc', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({pid}) });
  alert((await res.json()).msg || '操作完成');
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
  if (d.ok) { setTimeout(loadDocker, 2000); } else { alert('失败: ' + d.error); }
}

async function loadHistory() {
  const res = await fetch('/api/history');
  const d = await res.json();
  updateChart(d);
}

async function loadNetTest() {
  const btn = document.getElementById('retryBtn');
  btn.disabled = true; btn.innerText = '⏳ 测试中...';  
  ['local', 'alidns', 'tencentdns', 'baidudns', 'googledns', 'baidu'].forEach(id => { document.getElementById('test-' + id).innerText = '检测中...'; });
  const res = await fetch('/api/nettest');
  const d = await res.json();  
  document.getElementById('test-local').innerText = d.local;
  document.getElementById('test-alidns').innerText = d.alidns;
  document.getElementById('test-tencentdns').innerText = d.tencentdns;
  document.getElementById('test-baidudns').innerText = d.baidudns;
  document.getElementById('test-googledns').innerText = d.googledns;
  document.getElementById('test-baidu').innerText = d.baidu;
  document.getElementById('testTime').innerText = d.timestamp;
  btn.disabled = false; btn.innerText = '🔄 重新测试';
}

async function testGoogle() {
  const div = document.getElementById('googleResult');
  const btn = document.getElementById('googleBtn');
  div.innerText = '⏳ 正在测试 Google (Timeout 6s)...';
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
  btn.innerText = '💾 保存中...';
  const res = await fetch('/api/bashrc', { 
    method: 'POST', 
    headers: {'Content-Type': 'application/json'}, 
    body: JSON.stringify({content}) 
  });
  const d = await res.json();
  alert(d.msg || d.error);
  btn.disabled = false;
  btn.innerText = '💾 保存';
}

// OpenClaw 控制逻辑
async function checkOC() {
  const res = await fetch('/api/openclaw/status');
  const data = await res.json();
  const statusEl = document.getElementById('oc-status');
  statusEl.innerText = data.msg;
  statusEl.style.color = data.running ? 'green' : '#888';
}

async function startOC() {
  document.getElementById('oc-result').innerText = '正在启动...';
  const res = await fetch('/api/openclaw/start', { method: 'POST' });
  const data = await res.json();
  document.getElementById('oc-result').innerText = data.msg;
  setTimeout(checkOC, 3000);
}

async function stopOC() {
  document.getElementById('oc-result').innerText = '正在停止...';
  const res = await fetch('/api/openclaw/stop', { method: 'POST' });
  const data = await res.json();
  document.getElementById('oc-result').innerText = data.msg;
  setTimeout(checkOC, 2000);
}

async function doAction(action) {
  if (!confirm('确定执行操作: ' + action + '?\\n(注意：重启操作可能导致连接断开)')) return;
  const res = await fetch('/api/action/' + action, { method: 'POST' });
  const data = await res.json();
  document.getElementById('actionResult').innerText = data.msg || data.error;
}

setInterval(updateClock, 1000);
setInterval(() => { if(currentPage === 'monitor') loadStatus(); }, 2000);
setInterval(() => { if(currentPage === 'monitor') loadProcs(); }, 5000);
setInterval(() => { if(currentPage === 'monitor') loadHistory(); }, 5000);
setInterval(() => { if(currentPage === 'monitor') loadDocker(); }, 5000);
</script>
</body>
</html>`);
});

// --- 启动服务 ---
app.listen(port, () => {
  console.log(`✅ 面板启动完成 http://localhost:${port}`);
  console.log(`🔑 账号：${AUTH_USER} / 密码：${AUTH_PASS}`);
});
