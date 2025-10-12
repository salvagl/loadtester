const { spawn } = require('child_process');
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');
const fs = require('fs');

const SPEC_PATH = path.resolve(__dirname, 'openapi.json');
const PRISM_PORT = process.env.PRISM_PORT || 4010;
const LISTEN_PORT = process.env.PORT || 8000;

function startPrism() {
  console.log('Starting Prism mock server...');
 const prism = spawn('prism', ['mock', '--dynamic', '-h', '0.0.0.0', '-p', String(PRISM_PORT), SPEC_PATH], { stdio: 'inherit' });

  prism.on('error', err => console.error('Failed to start prism:', err));
  prism.on('exit', (code, sig) => console.log(`Prism exited with code=${code} sig=${sig}`));

  return prism;
}

function main() {
  const prismProcess = startPrism();

  const app = express();

  // Healthcheck
  app.get('/health', (req, res) => res.json({ status: 'ok' }));

  // ✅ Serve the OpenAPI spec directly
  app.get('/openapi.json', (req, res) => {
    res.setHeader('Content-Type', 'application/json');
    fs.createReadStream(SPEC_PATH).pipe(res);
  });

  // Proxy all other routes to Prism
  const target = `http://127.0.0.1:${PRISM_PORT}`;
  app.use('/', createProxyMiddleware({ target, changeOrigin: true, logLevel: 'warn' }));

  app.listen(LISTEN_PORT, '0.0.0.0', () => {
    console.log(`Mock proxy listening on ${LISTEN_PORT}, forwarding to ${target}`);
  });

  const shutdown = () => {
    console.log('Shutting down...');
    prismProcess.kill();
    process.exit(0);
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

main();
