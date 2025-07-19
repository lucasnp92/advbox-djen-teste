const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Log todas as requisições
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path} - IP: ${req.ip}`);
  next();
});

// Health check
app.get('/', (req, res) => {
  res.json({
    service: 'ADVBOX DJEN Proxy',
    status: 'online',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    description: 'Proxy service to bypass CloudFront restrictions for DJEN API',
    endpoints: {
      '/djen': 'GET - Proxy para API DJEN',
      '/health': 'GET - Health check'
    }
  });
});

// Health check específico
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Endpoint principal do proxy DJEN
app.get('/djen', async (req, res) => {
  try {
    console.log('📡 Nova requisição DJEN:', req.query);
    
    // Parâmetros da requisição
    const {
      nomeAdvogado = 'Eduardo Koetz',
      dataDisponibilizacaoInicio,
      dataDisponibilizacaoFim,
      itensPorPagina = '100',
      meio = 'D'
    } = req.query;
    
    // Validar parâmetros obrigatórios
    if (!dataDisponibilizacaoInicio || !dataDisponibilizacaoFim) {
      return res.status(400).json({
        success: false,
        error: 'Parâmetros obrigatórios: dataDisponibilizacaoInicio, dataDisponibilizacaoFim',
        received_params: req.query
      });
    }
    
    // Configurar requisição para API DJEN
    const apiUrl = 'https://comunicaapi.pje.jus.br/api/v1/comunicacao';
    const params = {
      nomeAdvogado,
      dataDisponibilizacaoInicio,
      dataDisponibilizacaoFim,
      itensPorPagina,
      meio
    };
    
    console.log('🌐 Fazendo requisição para DJEN API...');
    console.log('📋 Parâmetros:', params);
    
    // Fazer requisição com headers que funcionam
    const response = await axios.get(apiUrl, {
      params,
      timeout: 30000,
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'ADVBOX-Render-Proxy/1.0',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
      }
    });
    
    console.log('✅ Sucesso! Status:', response.status);
    console.log('📊 Total encontrado:', response.data.count);
    
    // Retornar dados formatados
    const resultado = {
      success: true,
      timestamp: new Date().toISOString(),
      proxy_info: {
        service: 'Render.com',
        method: 'axios_get',
        status_code: response.status,
        server_location: 'US/EU (Render)',
        parametros_enviados: params
      },
      api_response: response.data,
      stats: {
        total_intimacoes: response.data.count || 0,
        total_items: response.data.items ? response.data.items.length : 0
      }
    };
    
    res.json(resultado);
    
  } catch (error) {
    console.error('❌ Erro na requisição DJEN:', error.message);
    
    const errorInfo = {
      success: false,
      error: error.message,
      timestamp: new Date().toISOString(),
      debug_info: {
        service: 'Render.com',
        axios_error: error.response ? {
          status: error.response.status,
          statusText: error.response.statusText,
          headers: error.response.headers
        } : 'Network/timeout error',
        request_params: req.query
      }
    };
    
    // Status code baseado no erro
    const statusCode = error.response ? error.response.status : 500;
    res.status(statusCode).json(errorInfo);
  }
});

// Middleware para rotas não encontradas
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint não encontrado',
    available_endpoints: ['/', '/health', '/djen'],
    requested: req.originalUrl
  });
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`🚀 ADVBOX DJEN Proxy rodando na porta ${PORT}`);
  console.log(`📍 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`🌐 Endpoints disponíveis:`);
  console.log(`   - GET / (info do serviço)`);
  console.log(`   - GET /health (health check)`);
  console.log(`   - GET /djen (proxy DJEN API)`);
  console.log(`⏰ Iniciado em: ${new Date().toISOString()}`);
});