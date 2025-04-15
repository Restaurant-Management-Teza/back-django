const redis = require('ioredis');
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const axios = require('axios');
const rateLimit = require('express-rate-limit');
const loadBalancerUrl = 'http://nginx_load_balancer'; // Point to the load balancer
const httpProxy = require('http-proxy');
const Redis = require("ioredis");

const proxy = httpProxy.createProxyServer();
const app = express();
const PORT = process.env.PORT || 3000;

const cluster = new Redis.Cluster([
  { port: 7000, host: "redis-node-1" },
  { port: 7001, host: "redis-node-2" },
  { port: 7002, host: "redis-node-3" },
  { port: 7003, host: "redis-node-4" },
  { port: 7004, host: "redis-node-5" },
  { port: 7005, host: "redis-node-6" },
]);

// redisClient.connect().catch((err) => {
//     console.error("Redis connection error:", err);
// });

// Concurent task limiter
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 1000000, // limit each IP up to 100 reqs
    message: "Too many requests, please try again later.",
});

app.use(limiter);


// Cache middleware
const cacheMiddleware = async (req, res, next) => {
    const cacheKey = req.originalUrl;
    try {
        const cachedData = await cluster.get(cacheKey);
        if (cachedData) {
            console.log(`[Cache Hit] ${cacheKey}`);
            try {
                const data = JSON.parse(cachedData);
                return res.status(200).json(data);
            } catch (parseError) {
                console.error('Error parsing cached data:', parseError);
                await cluster.del(cacheKey); // Optional: Delete corrupted cache
                next();
            }
        } else {
            console.log(`[Cache Miss] ${cacheKey}`);
            next();
        }
    } catch (err) {
        console.error('Redis error:', err);
        next();
    }
};

// Proxy for Weather Data Service

app.use('/api/v1/health_wds', createProxyMiddleware({
    target: 'http://django-weather-data-service:8000',
    changeOrigin: true,
}));

// // Proxy for User Alert Service
// app.use('/api/v1/health_uas', createProxyMiddleware({
//     target: 'http://django-user-alert-service:8001',
//     changeOrigin: true,
// }));

app.use('/api/v1/current-weather', cacheMiddleware, async (req, res) => {
    const cacheKey = req.originalUrl;
    try {
        const response = await axios.get('http://django-user-alert-service:8001' + req.originalUrl);
        if (response.status === 200) {
            await cluster.set(cacheKey, JSON.stringify(response.data), 'EX', 60);
            res.status(200).json(response.data);
        } else {
            res.status(response.status).json({ error: response.statusText });
        }
    } catch (error) {
        if (error.response) {
            res.status(error.response.status).json({ error: error.response.statusText });
        } else if (error.request) {
            res.status(503).json({ error: 'No response from backend service' });
        } else {
            res.status(500).json({ error: 'Error setting up request to backend service' });
        }
    }
});



app.use('/api/v1/weather-prediction', cacheMiddleware, async (req, res) => {
    const cacheKey = req.originalUrl;
    try {
        const response = await axios.get('http://django-user-alert-service:8001' + req.originalUrl);
        if (response.status === 200) {
            await cluster.set(cacheKey, JSON.stringify(response.data), 'EX', 60);
            res.status(200).json(response.data);
        } else {
            res.status(response.status).json({ error: response.statusText });
        }
    } catch (error) {
        if (error.response) {
            res.status(error.response.status).json({ error: error.response.statusText });
        } else if (error.request) {
            res.status(503).json({ error: 'No response from backend service' });
        } else {
            res.status(500).json({ error: 'Error setting up request to backend service' });
        }
    }
});

app.get('/api/v1/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

async function postOnStart() {
  const anotherServiceUrl = 'http://service_discovery:5000/register';
  const payload = {
    name: 'gateway',
    ip: '127.0.0.1',
    port: '3000',
  };

  try {
    const response = await axios.post(anotherServiceUrl, payload);
    if (response.status === 200) {
      console.log('Successfully registered with the other service.');
    } else {
      console.error(`Failed to register with the other service. Status code: ${response.status}`);
    }
  } catch (error) {
    console.error(`Error registering with the other service: ${error.message}`);
  }
}

app.use((req, res) => {
  // Log the incoming request
  console.log(`Received request for: ${req.url}`);

  // Forward the request to the load balancer
  proxy.web(req, res, { target: loadBalancerUrl }, (error) => {
    console.error(`Error proxying request to ${loadBalancerUrl}:`, error);
    res.status(500).send('An error occurred while forwarding the request.');
  });
});


app.listen(PORT, () => {
    console.log(`Gateway listening on port ${PORT}`);
    postOnStart();
});
