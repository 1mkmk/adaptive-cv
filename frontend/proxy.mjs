// proxy.mjs - lokalny serwer proxy dla deweloperskiego środowiska
import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import cors from 'cors';
import http from 'http';
import https from 'https';

const app = express();
const PORT = 3001;

// Konfiguracja CORS
app.use(cors({
  origin: ['http://localhost:5173', 'http://localhost:3000'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept', 'Cookie'],
  exposedHeaders: ['Content-Length', 'Content-Type']
}));

// Utwórz agentów HTTP i HTTPS z dłuższymi timeoutami
const httpAgent = new http.Agent({
  keepAlive: true,
  timeout: 60000 // 60 sekund
});

const httpsAgent = new https.Agent({
  keepAlive: true,
  timeout: 60000 // 60 sekund
});

// Konfiguracja proxy do backendu z dłuższymi timeoutami
const apiProxy = createProxyMiddleware({
  target: 'http://localhost:8000',
  changeOrigin: true,
  pathRewrite: {
    '^/api': ''
  },
  ws: true, // Obsługa WebSocketów
  proxyTimeout: 30000, // 30 sekund timeout dla proxy
  timeout: 30000, // 30 sekund timeout dla żądań
  httpAgent,
  httpsAgent,
  onProxyReq: (proxyReq, req, res) => {
    // Log każdego żądania
    console.log(`[${new Date().toISOString()}] Proxying request: ${req.method} ${proxyReq.path}`);
    
    // Dodaj nagłówki dla debugowania CORS
    proxyReq.setHeader('Origin', 'http://localhost:5173');
    
    // Jeśli jest to żądanie POST/PUT z body, obsłuż je poprawnie
    if (req.body && (req.method === 'POST' || req.method === 'PUT')) {
      const bodyData = JSON.stringify(req.body);
      proxyReq.setHeader('Content-Type', 'application/json');
      proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData));
      proxyReq.write(bodyData);
    }
  },
  onProxyRes: (proxyRes, req, res) => {
    console.log(`[${new Date().toISOString()}] Received response from API: ${proxyRes.statusCode} for ${req.method} ${req.path}`);
    
    // Dodaj nagłówki CORS do odpowiedzi
    const origin = req.headers.origin;
    if (origin && (origin === 'http://localhost:5173' || origin === 'http://localhost:3000')) {
      proxyRes.headers['Access-Control-Allow-Origin'] = origin;
    }
    proxyRes.headers['Access-Control-Allow-Credentials'] = 'true';
    proxyRes.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS';
    proxyRes.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, Cookie';
  },
  onError: (err, req, res) => {
    console.error(`[${new Date().toISOString()}] Proxy error for ${req.method} ${req.url}:`, err);
    
    // Odpowiedz z sensownym błędem
    if (!res.headersSent) {
      res.status(500).json({
        error: true,
        message: 'Proxy Error: ' + err.message,
        code: err.code || 'UNKNOWN_ERROR'
      });
    }
  }
});

// Bezpośrednie sprawdzenie dostępności backendu
function checkBackendHealth() {
  http.get('http://localhost:8000', (res) => {
    console.log(`[${new Date().toISOString()}] Backend health check: Status ${res.statusCode}`);
  }).on('error', (err) => {
    console.error(`[${new Date().toISOString()}] Backend health check failed:`, err.message);
  });
}

// Sprawdź zdrowie backendu na starcie
checkBackendHealth();
// Sprawdzaj regularnie co 15 sekund
setInterval(checkBackendHealth, 15000);

// Parsuj dane JSON i URL-encoded
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Middleware do debugowania
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
});

// Wszystkie żądania do /api będą przekierowane do backendu
app.use('/api', apiProxy);

// Obsługa innych ścieżek
app.get('/', (req, res) => {
  res.json({
    status: 'ok',
    message: 'API Proxy Server for AdaptiveCV. Use /api/* to access backend endpoints.'
  });
});

// Obsługa błędów
app.use((err, req, res, next) => {
  console.error(`[${new Date().toISOString()}] Express error:`, err);
  res.status(500).json({
    error: true,
    message: err.message || 'Internal Server Error'
  });
});

// Uruchomienie serwera
const server = app.listen(PORT, () => {
  console.log(`[${new Date().toISOString()}] API Proxy Server running at http://localhost:${PORT}`);
  console.log(`[${new Date().toISOString()}] Access backend API via http://localhost:${PORT}/api/*`);
});

// Ustaw timeout dla serwera
server.timeout = 120000; // 2 minuty

// Obsługa zamknięcia
process.on('SIGINT', () => {
  console.log('Shutting down proxy server...');
  server.close(() => {
    console.log('Proxy server closed');
    process.exit(0);
  });
});