import express from 'express';
import { createProxyMiddleware, responseInterceptor } from 'http-proxy-middleware';
import cors from 'cors';

const app = express();
const PORT = 3001;

// 1) Globalny CORS dla wszystkich endpointów
app.use(cors({
  origin: ['http://localhost:5173','http://localhost:3000'],
  credentials: true,
  methods: ['GET','POST','PUT','DELETE','OPTIONS','PATCH'],
  allowedHeaders: ['Content-Type','Authorization','Accept','Cookie','Origin','X-Requested-With'],
  exposedHeaders: ['Content-Length','Content-Type','Authorization']
}));

// 2) Preflight dla /api
app.options('/api/*name', cors());

// 3) Body parsers
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 4) Debug log
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  next();
});

// 5) Proxy z ręcznym dopisaniem CORS
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:8000',
  changeOrigin: true,
  selfHandleResponse: true,
  onProxyRes: responseInterceptor(async (buffer, proxyRes, req, res) => {
    const origin = req.headers.origin || '*';
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Access-Control-Allow-Methods','GET,POST,PUT,DELETE,OPTIONS,PATCH');
    res.setHeader('Access-Control-Allow-Headers',
      'Content-Type,Authorization,Accept,Cookie,Origin,X-Requested-With'
    );
    return buffer;
  }),
  pathRewrite: { '^/api': '' },
  proxyTimeout: 120000,
  timeout: 120000,
  ws: true
}));

// 6) Root health check
app.get('/', (req, res) => {
  res.json({ status: 'ok', message: 'Proxy działa. Użyj /api/*' });
});

const server = app.listen(PORT, () => {
  console.log(`Proxy running at http://localhost:${PORT}`);
});
server.timeout = 180000;
