#!/usr/bin/env python3
"""
🚀 API Server DJEN - Eduardo Koetz
Servidor API simples para integração com N8N webhook
"""

import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import threading
import logging
import schedule
import time

# Adicionar o diretório atual ao path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos do projeto
from djen_extractor import DJENExtractor
import config
from logging_config import setup_logging

# Configurar Flask
app = Flask(__name__)

# Configurar CORS para permitir acesso do webhook
CORS(app, origins=["https://webhook.lnpassos.com.br", "http://localhost:*", "http://127.0.0.1:*", "http://172.20.119.188:*"], 
     methods=['GET', 'POST', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'])

# Configurar logging
logger = setup_logging()

# Instância global do extrator
extractor = None

def inicializar_extractor():
    """Inicializar o extrator DJEN"""
    global extractor
    try:
        extractor = DJENExtractor()
        logger.info("✅ DJENExtractor inicializado para API server")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar extrator: {e}")
        extractor = None

@app.route('/status', methods=['GET'])
def get_status():
    """Endpoint para obter status do sistema"""
    try:
        if not extractor:
            return jsonify({
                'status': 'error',
                'erro': 'Sistema não inicializado',
                'sistema_funcional': False
            }), 500
        
        # Obter estatísticas do Supabase
        stats = extractor.supabase_client.obter_estatisticas()
        
        # Obter última execução
        logs = extractor.supabase_client.obter_logs_execucao(limite=1)
        ultima_extracao = 'Nunca'
        if logs:
            ultima_extracao = logs[0].get('data_extracao', 'Nunca')
            if ultima_extracao != 'Nunca':
                try:
                    dt = datetime.fromisoformat(ultima_extracao.replace('Z', '+00:00'))
                    ultima_extracao = dt.strftime('%d/%m %H:%M')
                except:
                    pass
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'sistema_funcional': True,
            'total_intimacoes': stats.get('total_intimacoes', 0),
            'tribunais_ativos': stats.get('tribunais_unicos', 0),
            'ultima_extracao': ultima_extracao
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        return jsonify({
            'status': 'error',
            'erro': str(e),
            'sistema_funcional': False
        }), 500

@app.route('/testar', methods=['GET'])
def testar_sistema():
    """Endpoint para testar componentes do sistema"""
    try:
        if not extractor:
            return jsonify({
                'status': 'error',
                'erro': 'Sistema não inicializado',
                'api': False,
                'supabase': False,
                'text_processor': False
            }), 500
        
        # Executar testes dos componentes
        testes = extractor.testar_componentes()
        
        return jsonify({
            'status': 'success',
            'api': testes.get('api', False),
            'supabase': testes.get('supabase', False),
            'text_processor': testes.get('text_processor', False),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar sistema: {e}")
        return jsonify({
            'status': 'error',
            'erro': str(e),
            'api': False,
            'supabase': False,
            'text_processor': False
        }), 500

@app.route('/extrair', methods=['POST'])
def executar_extracao():
    """Endpoint para executar extração manual"""
    def extrair_async():
        try:
            logger.info("🚀 Iniciando extração via API webhook...")
            resultado = extractor.executar_extracao_diaria()
            logger.info(f"✅ Extração concluída via webhook: {resultado}")
        except Exception as e:
            logger.error(f"❌ Erro na extração via webhook: {e}")
    
    try:
        if not extractor:
            return jsonify({
                'status': 'erro',
                'erro': 'Sistema não inicializado'
            }), 500
        
        # Executar extração em thread separada
        thread = threading.Thread(target=extrair_async)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'sucesso',
            'mensagem': 'Extração iniciada em segundo plano',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao iniciar extração: {e}")
        return jsonify({
            'status': 'erro',
            'erro': str(e)
        }), 500

@app.route('/intimacoes', methods=['GET'])
def get_intimacoes():
    """Endpoint para buscar intimações"""
    try:
        if not extractor:
            return jsonify({'erro': 'Sistema não inicializado'}), 500
        
        # Parâmetros opcionais
        limite = request.args.get('limit', 10, type=int)
        data = request.args.get('data')
        eduardo_unico = request.args.get('eduardo_unico', 'false').lower() == 'true'
        
        # Buscar intimações no Supabase
        intimacoes = extractor.supabase_client.buscar_intimacoes(
            limite=limite,
            data_especifica=data
        )
        
        # Filtrar por Eduardo único se solicitado
        if eduardo_unico:
            intimacoes_filtradas = []
            for intimacao in intimacoes:
                texto = intimacao.get('conteudo_texto', '')
                if extractor.text_processor.eh_eduardo_unico_advogado(texto):
                    intimacoes_filtradas.append(intimacao)
            intimacoes = intimacoes_filtradas
        
        return jsonify(intimacoes)
        
    except Exception as e:
        logger.error(f"Erro ao buscar intimações: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/estatisticas/tribunal', methods=['GET'])
def get_estatisticas_tribunal():
    """Endpoint para estatísticas por tribunal"""
    try:
        if not extractor:
            return jsonify({'erro': 'Sistema não inicializado'}), 500
        
        stats = extractor.supabase_client.obter_estatisticas_tribunal()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas por tribunal: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """Endpoint para buscar logs de execução"""
    try:
        if not extractor:
            return jsonify({'erro': 'Sistema não inicializado'}), 500
        
        limite = request.args.get('limit', 10, type=int)
        logs = extractor.supabase_client.obter_logs_execucao(limite=limite)
        
        return jsonify(logs)
        
    except Exception as e:
        logger.error(f"Erro ao buscar logs: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check para monitoramento"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'sistema_inicializado': extractor is not None
    })

@app.route('/scheduler/status', methods=['GET'])
def scheduler_status():
    """Status do agendador de extração automática"""
    try:
        jobs = schedule.get_jobs()
        proximo_job = None
        
        if jobs:
            proximo_job = jobs[0].next_run.isoformat() if jobs[0].next_run else None
        
        return jsonify({
            'status': 'active' if jobs else 'inactive',
            'jobs_agendados': len(jobs),
            'proxima_execucao': proximo_job,
            'horario_configurado': '06:00 (diário)',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter status do scheduler: {e}")
        return jsonify({
            'status': 'error',
            'erro': str(e)
        }), 500

@app.route('/')
def index():
    """Servir a página principal do painel"""
    try:
        return send_from_directory('.', 'painel_local.html')
    except Exception as e:
        logger.error(f"Erro ao servir página principal: {e}")
        return jsonify({'erro': 'Página não encontrada'}), 404

# Middleware para log de requisições
@app.before_request
def log_request_info():
    logger.info(f"API Request: {request.method} {request.url} - Origin: {request.headers.get('Origin', 'N/A')}")

@app.after_request
def log_response_info(response):
    logger.info(f"API Response: {response.status_code}")
    return response

@app.errorhandler(404)
def not_found(error):
    return jsonify({'erro': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'erro': 'Erro interno do servidor'}), 500

def executar_extracao_automatica():
    """Função para executar extração automática diária"""
    try:
        hora_atual = datetime.now().strftime("%H:%M:%S")
        data_atual = datetime.now().strftime("%d/%m/%Y")
        
        logger.info(f"🕐 [{hora_atual}] Iniciando extração automática diária para {data_atual}")
        print(f"🕐 [{hora_atual}] Iniciando extração automática diária para {data_atual}")
        
        if not extractor:
            logger.error("❌ Extrator não inicializado para execução automática")
            return
        
        # Executar extração
        resultado = extractor.executar_extracao_diaria()
        
        logger.info(f"✅ Extração automática concluída: {resultado}")
        print(f"✅ Extração automática concluída: {resultado}")
        
        # Log adicional sobre próxima execução
        proxima_execucao = "06:00 (próximo dia)"
        logger.info(f"📅 Próxima extração automática: {proxima_execucao}")
        print(f"📅 Próxima extração automática: {proxima_execucao}")
        
    except Exception as e:
        logger.error(f"❌ Erro na extração automática: {e}")
        print(f"❌ Erro na extração automática: {e}")

def iniciar_agendador():
    """Inicializa o agendador de extrações automáticas"""
    try:
        # Agendar extração para todo dia às 6:00 AM
        schedule.every().day.at("06:00").do(executar_extracao_automatica)
        
        logger.info("📅 Agendador iniciado - Extração automática configurada para 06:00 diariamente")
        print("📅 Agendador iniciado - Extração automática configurada para 06:00 diariamente")
        
        # 🧪 MODO TESTE (descomente as linhas abaixo para testar):
        # Para executar em 2 minutos após inicializar:
        # schedule.every(2).minutes.do(executar_extracao_automatica)
        # logger.info("🧪 MODO TESTE: Executará em 2 minutos + diariamente às 06:00")
        # print("🧪 MODO TESTE: Executará em 2 minutos + diariamente às 06:00")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto
            
    except Exception as e:
        logger.error(f"❌ Erro no agendador: {e}")
        print(f"❌ Erro no agendador: {e}")

def main():
    """Função principal para iniciar o servidor API"""
    print("🚀 Iniciando API Server DJEN...")
    print("=" * 60)
    print("🌐 Integração com N8N webhook: https://webhook.lnpassos.com.br/webhook/demo2")
    
    # Inicializar o extrator
    print("🔧 Inicializando sistema DJEN...")
    inicializar_extractor()
    
    if not extractor:
        print("❌ Falha ao inicializar sistema DJEN!")
        sys.exit(1)
    
    print("✅ Sistema DJEN inicializado com sucesso!")
    
    # Inicializar agendador automático em thread separada
    print("📅 Iniciando agendador de extração automática...")
    scheduler_thread = threading.Thread(target=iniciar_agendador, daemon=True)
    scheduler_thread.start()
    print("✅ Agendador iniciado em background")
    
    print("🔗 API disponível em: http://localhost:8000")
    print("🌐 Painel web: http://172.20.119.188:8000")
    print("📋 Endpoints disponíveis:")
    print("  - GET  /status")
    print("  - GET  /testar")
    print("  - POST /extrair")
    print("  - GET  /intimacoes")
    print("  - GET  /estatisticas/tribunal")
    print("  - GET  /logs")
    print("  - GET  /health")
    print("  - GET  /scheduler/status")
    print("⏰ EXTRAÇÃO AUTOMÁTICA: Todos os dias às 06:00")
    print("=" * 60)
    
    try:
        # Iniciar servidor Flask
        app.run(
            host='0.0.0.0',  # Permitir conexões externas
            port=8000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 API Server interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()