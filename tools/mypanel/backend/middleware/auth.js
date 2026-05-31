const AUTH_USER = process.env.MONITOR_USER;
const AUTH_PASS = process.env.MONITOR_PASS;

function checkAuth(req, res, next) {
  if (!AUTH_USER || !AUTH_PASS) {
    res.setHeader('WWW-Authenticate', 'Basic realm="Login"');
    return res.status(503).send(
      'Authentication not configured. Set MONITOR_USER and MONITOR_PASS environment variables.'
    );
  }
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Basic ')) {
    res.setHeader('WWW-Authenticate', 'Basic realm="Login"');
    return res.status(401).send('Unauthorized');
  }
  try {
    const decoded = Buffer.from(auth.split(' ')[1], 'base64').toString();
    const colonIndex = decoded.indexOf(':');
    if (colonIndex === -1) {
      return res.status(401).send('Invalid credentials format');
    }
    const user = decoded.substring(0, colonIndex);
    const pass = decoded.substring(colonIndex + 1);
    if (user === AUTH_USER && pass === AUTH_PASS) return next();
  } catch (e) {
    return res.status(401).send('Invalid credentials');
  }
  return res.status(401).send('Wrong Password');
}

module.exports = { checkAuth };
