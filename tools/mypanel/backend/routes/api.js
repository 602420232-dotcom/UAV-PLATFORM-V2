const express = require('express');
const { execSync } = require('child_process');

const { checkAuth } = require('../middleware/auth');
const { getStatus, getHistoryData, clearTraffic } = require('../services/monitor');
const { isAvailable, listContainers, getContainerStats, containerAction } = require('../services/docker');

const apiRouter = express.Router();

apiRouter.get('/status', checkAuth, async (req, res) => {
  res.json(await getStatus());
});

apiRouter.get('/history', checkAuth, (req, res) => {
  res.json(getHistoryData());
});

apiRouter.get('/procs', checkAuth, (req, res) => {
  try {
    const out = execSync("ps aux --sort=-%cpu | head -11 | awk '{print $1,$2,$3,$4,$11}'").toString();
    const lines = out.trim().split('\n');
    const data = lines.map(line => {
      const parts = line.trim().split(/\s+/);
      return { user: parts[0], pid: parts[1], cpu: parts[2], mem: parts[3], cmd: parts.slice(4).join(' ') };
    });
    res.json(data);
  } catch (e) { res.json([]); }
});

apiRouter.get('/docker', checkAuth, async (req, res) => {
  if (!isAvailable()) return res.json([]);
  try {
    const containers = await listContainers();
    res.json(containers);
  } catch (e) { res.json([]); }
});

apiRouter.get('/docker/stats', checkAuth, async (req, res) => {
  const stats = await getContainerStats();
  res.json(stats);
});

apiRouter.post('/docker/:id/:action', checkAuth, async (req, res) => {
  if (!isAvailable()) return res.status(503).json({ error: 'Docker not available' });
  const { id, action } = req.params;
  try {
    await containerAction(id, action);
    res.json({ ok: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

apiRouter.get('/nettest', checkAuth, (req, res) => {
  const result = { timestamp: new Date().toLocaleTimeString('zh-CN') };
  const tests = [
    ['local', '127.0.0.1'],
    ['alidns', '223.5.5.5'],
    ['tencentdns', '119.29.29.29'],
    ['baidudns', '180.76.76.76'],
    ['googledns', '8.8.8.8'],
    ['baidu', 'www.baidu.com']
  ];
  tests.forEach(([key, host]) => {
    try {
      execSync(`ping -c 1 -W 1 ${host}`, { timeout: 2000 });
      result[key] = '\u2705 \u6b63\u5e38';
    } catch (e) {
      result[key] = '\u274c \u5f02\u5e38';
    }
  });
  res.json(result);
});

apiRouter.get('/test-google', checkAuth, (req, res) => {
  try {
    const gateway = execSync("ip route | awk '/default/ {print $3; exit}'").toString().trim();
    if (!gateway) return res.json({ success: false, msg: '\u274c \u65e0\u6cd5\u83b7\u53d6\u7f51\u5173 IP' });
    const cmd = `curl -I -m 6 -x http://${gateway}:7890 https://www.google.com 2>&1`;
    const out = execSync(cmd, { timeout: 8000 }).toString();
    if (out.includes('HTTP/') && !out.includes('407 Proxy Authentication Required')) {
      const statusLine = out.split('\n')[0];
      res.json({ success: true, msg: `\u2705 \u8fde\u63a5\u6210\u529f (via ${gateway}): ${statusLine}` });
    } else {
      res.json({ success: false, msg: `\u274c \u8fde\u63a5\u5931\u8d25: ${out.substring(0, 150)}` });
    }
  } catch (e) {
    let errMsg = e.stderr ? e.stderr.toString() : e.message;
    if (errMsg.includes('timed out')) errMsg = '\u8fde\u63a5\u8d85\u65f6 (\u4ee3\u7406\u672a\u5f00/\u7aef\u53e3\u9519)';
    if (errMsg.includes('Refused')) errMsg = '\u8fde\u63a5\u88ab\u62d2 (Clash \u672a\u5f00 Allow LAN)';
    res.json({ success: false, msg: '\u274c ' + errMsg });
  }
});

apiRouter.get('/test-github', checkAuth, (req, res) => {
  try {
    const cmd = `curl -s -I -L -m 6 https://github.com 2>&1`;
    const out = execSync(cmd, { timeout: 8000 }).toString();
    if (/^HTTP\/\d[\d.]*\s+(200|301|302)/m.test(out)) {
      const statusLine = out.match(/^(HTTP\/\S+\s+\d+.*)$/m);
      const msg = statusLine ? statusLine[1] : 'OK';
      res.json({ success: true, msg: `\u2705 GitHub \u53ef\u8fbe: ${msg}` });
    } else {
      res.json({ success: false, msg: `\u274c GitHub \u4e0d\u53ef\u8fbe: ${out.substring(0, 150)}` });
    }
  } catch (e) {
    let errMsg = (e.stderr || e.message || '').toString();
    if (/timed out|Timeout/i.test(errMsg)) {
      errMsg = '\u8fde\u63a5\u8d85\u65f6 (\u68c0\u67e5 Clash/TUN \u6a21\u5f0f\u662f\u5426\u5f00\u542f)';
    }
    res.json({ success: false, msg: `\u274c ${errMsg.substring(0, 200)}` });
  }
});

apiRouter.get('/speedtest', checkAuth, (req, res) => {
  try {
    const url = 'https://httpbin.org/stream-bytes/1048576';
    const out = execSync(
      `curl -s -o /dev/null -w '__SPD__%{speed_download}__TIME__%{time_total}' --max-time 25 "${url}" 2>&1`,
      { timeout: 30000 }
    ).toString();

    const spd = out.match(/__SPD__([\d.]+)/);
    const tim = out.match(/__TIME__([\d.]+)/);
    if (!spd || !tim) return res.json({ success: false, msg: `\u274c \u89e3\u6790\u5931\u8d25: ${out.slice(0, 250)}` });

    const bps = Number(spd[1]);
    const sec = Number(tim[1]);
    const mBps = (bps / 1024 / 1024).toFixed(2);
    const kBps = (bps / 1024).toFixed(1);
    return res.json({
      success: true,
      msg: `\ud83d\ude80 \u7ea6 ${mBps} MB/s\uff08${kBps} KB/s\uff09\uff0c\u8017\u65f6 ${sec.toFixed(2)}s\uff08\u4e0b\u8f7d\u6837\u672c 1MB\uff09`
    });
  } catch (e) {
    const em = (e.stderr || e.message || '').toString();
    if (/timed out|Timeout/i.test(em)) return res.json({ success: false, msg: '\u274c \u6d4b\u901f\u8d85\u65f6\uff08>25s\uff09' });
    return res.json({ success: false, msg: `\u274c ${em.slice(0, 250)}` });
  }
});

apiRouter.get('/bashrc', checkAuth, (req, res) => {
  const fs = require('fs');
  const os = require('os');
  try {
    const content = fs.readFileSync(os.homedir() + '/.bashrc', 'utf8');
    res.json({ content });
  } catch (e) {
    res.json({ content: '# \u65e0\u6cd5\u8bfb\u53d6\u6587\u4ef6', error: e.message });
  }
});

apiRouter.post('/bashrc', checkAuth, (req, res) => {
  const fs = require('fs');
  const os = require('os');
  const { content } = req.body;
  if (!content) return res.status(400).json({ error: '\u5185\u5bb9\u4e3a\u7a7a' });
  try {
    fs.writeFileSync(os.homedir() + '/.bashrc', content);
    try {
      execSync(`bash -c "source ${os.homedir()}/.bashrc"`);
      res.json({ msg: '\u2705 \u4fdd\u5b58\u6210\u529f\uff01\u914d\u7f6e\u5df2\u5199\u5165\u3002\u8bf7\u91cd\u542f\u76f8\u5173\u670d\u52a1\uff08\u5982 OpenClaw\uff09\u4ee5\u751f\u6548\u3002' });
    } catch (sourceErr) {
      res.json({ msg: `\u26a0\ufe0f \u4fdd\u5b58\u6210\u529f\uff0c\u4f46\u91cd\u8f7d\u914d\u7f6e\u65f6\u62a5\u9519\uff1a${sourceErr.message.substring(0, 100)}` });
    }
  } catch (e) {
    res.status(500).json({ error: '\u6587\u4ef6\u5199\u5165\u5931\u8d25: ' + e.message });
  }
});

apiRouter.post('/action/:action', checkAuth, (req, res) => {
  const { action } = req.params;
  try {
    switch (action) {
      case 'clear-traffic':
        clearTraffic();
        return res.json({ msg: '\u2705 \u6d41\u91cf\u7edf\u8ba1\u5df2\u6e05\u96f6' });
      case 'kill-proc':
        process.kill(parseInt(req.body.pid), 'SIGTERM');
        return res.json({ msg: `\u2705 \u8fdb\u7a0b ${req.body.pid} \u5df2\u7ec8\u6b62` });
      case 'restart-panel':
        if (process.env.PM2_HOME || process.env.pm_id) {
          res.json({ msg: '\u2705 \u9762\u677f\u6b63\u5728\u91cd\u542f...' });
          setTimeout(() => process.exit(0), 1000);
        } else {
          res.json({ msg: '\u26a0\ufe0f \u975e PM2 \u73af\u5883\uff0c\u8bf7\u624b\u52a8\u91cd\u542f' });
        }
        break;
      case 'restart-docker':
        execSync('sudo service docker restart');
        return res.json({ msg: '\u2705 Docker \u6b63\u5728\u91cd\u542f...' });
      case 'restart-wsl':
        res.json({ msg: '\u26a0\ufe0f WSL \u6b63\u5728\u91cd\u542f\uff0c\u8fde\u63a5\u5373\u5c06\u65ad\u5f00...' });
        setTimeout(() => execSync('shutdown -r now'), 1000);
        break;
      default:
        return res.status(400).json({ error: '\u672a\u77e5\u64cd\u4f5c' });
    }
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
});

function checkOCStatus() {
  try {
    execSync('pgrep -f "openclaw/dist/index.js"');
    return true;
  } catch (e) {
    return false;
  }
}

apiRouter.get('/openclaw/status', checkAuth, (req, res) => {
  const running = checkOCStatus();
  res.json({
    running,
    msg: running ? '\ud83e\udd9e OpenClaw \u6b63\u5728\u8fd0\u884c' : '\u26ab OpenClaw \u672a\u8fd0\u884c'
  });
});

apiRouter.post('/openclaw/start', checkAuth, (req, res) => {
  const { spawn } = require('child_process');
  const fs = require('fs');
  try {
    if (checkOCStatus()) {
      return res.json({ success: false, msg: '\u5df2\u7ecf\u5728\u8fd0\u884c\u4e86' });
    }
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
    res.json({ success: true, msg: '\ud83d\ude80 OpenClaw \u6b63\u5728\u540e\u53f0\u542f\u52a8...' });
  } catch (e) {
    res.json({ success: false, msg: '\u542f\u52a8\u5931\u8d25: ' + e.message });
  }
});

apiRouter.post('/openclaw/stop', checkAuth, (req, res) => {
  try {
    execSync('pkill -f openclaw');
    res.json({ success: true, msg: '\ud83d\uded1 OpenClaw \u5df2\u505c\u6b62' });
  } catch (e) {
    res.json({ success: false, msg: '\u505c\u6b62\u5931\u8d25\u6216\u8fdb\u7a0b\u4e0d\u5b58\u5728' });
  }
});

module.exports = { apiRouter };
