const { initDocker } = require('./backend/services/docker');
const { app, port } = require('./backend/server');

initDocker();

app.listen(port, () => {
  console.log(`Monitor panel running on http://localhost:${port}`);
});
