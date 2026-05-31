const express = require('express');
const path = require('path');
const app = express();
const port = process.env.MONITOR_PORT || 5577;

app.use(express.static(path.join(__dirname, '..', 'public')));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use((req, res, next) => {
  res.set('Cache-Control', 'no-store, no-cache, must-revalidate');
  next();
});

const { apiRouter } = require('./routes/api');
app.use('/api', apiRouter);

const { pageRouter } = require('./routes/pages');
app.use('/', pageRouter);

const { initMonitor } = require('./services/monitor');
initMonitor();

module.exports = { app, port };
