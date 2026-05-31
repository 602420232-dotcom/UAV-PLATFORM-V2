const os = require('os');
const fs = require('fs');
const { execSync } = require('child_process');
const disk = require('diskusage');

const AUTH_USER = process.env.MONITOR_USER || 'admin';
const AUTH_PASS = process.env.MONITOR_PASS || 'admin123';
const TRAFFIC_FILE = __dirname + '/../../traffic.json';
const MAX_HISTORY = 60;

let traffic = loadTraffic();
let lastRx = 0n, lastTx = 0n;
let netRxSpeed = 0, netTxSpeed = 0;
let historyData = { cpu: [], mem: [], netRx: [], gpu: [], time: [] };

function loadTraffic() {
  try {
    if (fs.existsSync(TRAFFIC_FILE)) {
      return JSON.parse(fs.readFileSync(TRAFFIC_FILE, 'utf8'));
    }
  } catch (e) {}
  return { totalRx: 0, totalTx: 0 };
}

function saveTraffic(rx, tx) {
  traffic = { totalRx: rx, totalTx: tx };
  fs.writeFileSync(TRAFFIC_FILE, JSON.stringify(traffic, null, 2));
}

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

  let gpuUsage = 'N/A';
  try {
    const cmd = 'which nvidia-smi > /dev/null 2>&1 && nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits || echo "N/A"';
    const gpuOut = execSync(cmd, { timeout: 1500 }).toString().trim();
    if (gpuOut !== 'N/A' && !isNaN(parseInt(gpuOut))) gpuUsage = parseInt(gpuOut);
  } catch (e) {}

  let ipInfo = { address: 'N/A', gateway: 'N/A', proxy: '\u672a\u8bbe\u7f6e', httpsProxy: '\u672a\u8bbe\u7f6e' };
  try {
    const route = execSync('ip route | grep default').toString().trim();
    const match = route.match(/via\s+([\d.]+)/);
    if (match) ipInfo.gateway = match[1];

    const addr = execSync("ip addr show eth0 | grep 'inet ' | awk '{print $2}'").toString().trim();
    if (addr) ipInfo.address = addr;

    if (ipInfo.gateway) {
      try {
        execSync(`nc -z -w1 ${ipInfo.gateway} 7890 2>/dev/null`, { timeout: 1500 });
        ipInfo.proxy = `http://${ipInfo.gateway}:7890 (\u8fd0\u884c\u4e2d)`;
        ipInfo.httpsProxy = `http://${ipInfo.gateway}:7890 (\u8fd0\u884c\u4e2d)`;
      } catch (proxyErr) {
        ipInfo.proxy = `http://${ipInfo.gateway}:7890 (\u672a\u8fd0\u884c)`;
        ipInfo.httpsProxy = `http://${ipInfo.gateway}:7890 (\u672a\u8fd0\u884c)`;
      }
    }
  } catch (e) {}

  const now = new Date().toLocaleTimeString('zh-CN', { hour12: false });
  historyData.cpu.push(parseFloat(cpu[0]));
  historyData.mem.push(parseFloat(memUsage));
  historyData.gpu.push(typeof gpuUsage === 'number' ? gpuUsage : 0);
  historyData.time.push(now);
  if (historyData.cpu.length > MAX_HISTORY) {
    historyData.cpu.shift(); historyData.mem.shift();
    historyData.gpu.shift(); historyData.time.shift();
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

function initTrafficMonitor() {
  setInterval(() => {
    try {
      const data = fs.readFileSync('/proc/net/dev', 'utf8');
      for (const line of data.split('\n')) {
        if (line.includes('eth0')) {
          const p = line.trim().split(/\s+/);
          const rx = BigInt(p[1]), tx = BigInt(p[9]);

          if (lastRx === 0n) { lastRx = rx; lastTx = tx; return; }
          if (rx < lastRx || tx < lastTx) { lastRx = rx; lastTx = tx; return; }

          const r = Number(rx - lastRx), t = Number(tx - lastTx);
          traffic.totalRx += r; traffic.totalTx += t;
          saveTraffic(traffic.totalRx, traffic.totalTx);
          netRxSpeed = (r / 1024).toFixed(2);
          netTxSpeed = (t / 1024).toFixed(2);
          lastRx = rx; lastTx = tx;
        }
      }
    } catch (e) {}
  }, 1000);
}

function clearTraffic() {
  saveTraffic(0, 0);
  lastRx = 0n; lastTx = 0n;
}

function getTraffic() { return traffic; }
function getHistoryData() { return historyData; }

module.exports = {
  getStatus, getHistoryData, getTraffic,
  initTrafficMonitor, clearTraffic,
  initMonitor: initTrafficMonitor
};
