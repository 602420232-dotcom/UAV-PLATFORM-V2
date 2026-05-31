const Docker = require('dockerode');

let docker = null;
let isDockerAvailable = false;

function initDocker() {
  try {
    docker = new Docker({ socketPath: '/var/run/docker.sock' });
    docker.info((err, info) => {
      if (err) {
        console.warn('Docker installed but cannot connect (may not be running):', err.message);
        isDockerAvailable = false;
      } else {
        console.log('Docker connected successfully');
        isDockerAvailable = true;
      }
    });
  } catch (e) {
    console.warn('Docker module failed to load');
  }
}

function isAvailable() {
  return isDockerAvailable && docker !== null;
}

function getDocker() {
  return docker;
}

async function listContainers() {
  if (!isAvailable()) return [];
  try {
    return await docker.listContainers({ all: true });
  } catch (e) {
    return [];
  }
}

async function getContainerStats() {
  if (!isAvailable()) return {};
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
        const netRx = stats.networks ? Object.values(stats.networks).reduce((a, b) => a + b.rx_bytes, 0) : 0;
        const netTx = stats.networks ? Object.values(stats.networks).reduce((a, b) => a + b.tx_bytes, 0) : 0;
        result[c.Id] = { cpuPercent, memPercent, memMB, netRx, netTx };
      } catch (e) {}
    }));
    return result;
  } catch (e) {
    return {};
  }
}

async function containerAction(id, action) {
  if (!isAvailable()) throw new Error('Docker not available');
  const ct = docker.getContainer(id);
  switch (action) {
    case 'start': await ct.start(); break;
    case 'stop': await ct.stop(); break;
    case 'restart': await ct.restart(); break;
    default: throw new Error(`Invalid action: ${action}`);
  }
}

module.exports = {
  initDocker, isAvailable, getDocker,
  listContainers, getContainerStats, containerAction
};
