const express = require('express');
const fs = require('fs');
const path = require('path');

const { checkAuth } = require('../middleware/auth');

const pageRouter = express.Router();

const html = fs.readFileSync(path.join(__dirname, '../../public/index.html'), 'utf8');

pageRouter.get('/', checkAuth, (req, res) => {
  res.send(html);
});

module.exports = { pageRouter };
