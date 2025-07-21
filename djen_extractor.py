"""
Sistema principal de extração DJEN
Integra API, processamento de texto, deduplicação e armazenamento
"""
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from djen_api import DJENApiClient
from text_processor import TextProcessor
from supabase_client import SupabaseClient
from config import validar_configuracoes

class DJENExtractor:
    """
    Classe principal que coordena toda a extração DJEN
    """
    
    def __init__(self):
        # Validar configurações
        validar_configuracoes()
        
        # Inicializar componentes
        self.api_client = DJENApiClient()
        self.text_processor = TextProcessor()
        self.supabase_client = SupabaseClient()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("✅ DJENExtractor inicializado")
    
    def testar_componentes(self) -> Dict[str, bool]:
        """
        Testa todos os componentes do sistema
        
        Returns:
            Dict[str, bool]: Status de cada componente
        """
        testes = {}
        
        self.logger.info("🔍 Testando componentes do sistema...")
        
        # Teste da API
        try:
            testes['api'] = self.api_client.testar_conectividade()
        except Exception as e:
            self.logger.error(f"Erro no teste da API: {e}")
            testes['api'] = False
        
        # Teste do Supabase
        try:
            testes['supabase'] = self.supabase_client.testar_conexao()
        except Exception as e:
            self.logger.error(f"Erro no teste do Supabase: {e}")
            testes['supabase'] = False
        
        # Teste do processador de texto
        try:
            texto_teste = "<p>Teste de <b>processamento</b><br>com HTML</p>"
            resultado = self.text_processor.processar_texto(texto_teste)
            testes['text_processor'] = len(resultado) > 0 and '<' not in resultado
        except Exception as e:
            self.logger.error(f"Erro no teste do processador: {e}")
            testes['text_processor'] = False
        
        # Resumo dos testes
        todos_ok = all(testes.values())
        self.logger.info(f"Testes concluídos: {testes}")
        
        if todos_ok:
            self.logger.info("✅ Todos os componentes funcionando")
        else:
            self.logger.warning("⚠️ Alguns componentes com problemas")
        
        return testes
    
    def executar_extracao_diaria(
        self, 
        data_inicio: Optional[str] = None, 
        data_fim: Optional[str] = None
    ) -> Dict:
        """
        Executa a extração diária completa
        
        Args:
            data_inicio: Data de início (opcional)
            data_fim: Data de fim (opcional)
            
        Returns:
            Dict: Relatório de execução
        """
        inicio_execucao = time.time()
        
        self.logger.info("🚀 Iniciando extração diária DJEN")
        
        relatorio = {
            "inicio_execucao": datetime.now().isoformat(),
            "status_execucao": "em_andamento",
            "total_encontradas": 0,
            "total_novas": 0,
            "total_duplicadas": 0,
            "total_erros": 0,
            "tempo_execucao_segundos": 0,
            "parametros_busca": {
                "data_inicio": data_inicio,
                "data_fim": data_fim
            },
            "detalhes_erros": []
        }
        
        try:
            # Passo 1: Buscar intimações na API
            self.logger.info("📡 Buscando intimações na API...")
            sucesso_api, intimacoes_raw = self.api_client.buscar_todas_oabs_eduardo(
                data_inicio=data_inicio, 
                data_fim=data_fim
            )
            
            if not sucesso_api:
                raise Exception("Falha na consulta da API DJEN")
            
            relatorio["total_encontradas"] = len(intimacoes_raw)
            self.logger.info(f"📋 Total encontrado na API: {len(intimacoes_raw)}")
            
            if not intimacoes_raw:
                self.logger.info("ℹ️ Nenhuma intimação encontrada para o período")
                relatorio["status_execucao"] = "sucesso"
                return relatorio
            
            # Passo 2: Processar intimações
            self.logger.info("⚙️ Processando intimações...")
            intimacoes_processadas = []
            
            for item_raw in intimacoes_raw:
                try:
                    intimacao_processada = self.text_processor.processar_intimacao_completa(item_raw)
                    
                    # Validar intimação
                    if self.text_processor.validar_intimacao(intimacao_processada):
                        intimacoes_processadas.append(intimacao_processada)
                    else:
                        self.logger.warning(f"Intimação {item_raw.get('id')} falhou na validação")
                        relatorio["total_erros"] += 1
                
                except Exception as e:
                    self.logger.error(f"Erro ao processar intimação {item_raw.get('id')}: {e}")
                    relatorio["total_erros"] += 1
                    relatorio["detalhes_erros"].append(str(e))
            
            self.logger.info(f"✅ Processadas {len(intimacoes_processadas)} intimações válidas")
            
            # Passo 3: Armazenar no Supabase (com deduplicação automática)
            self.logger.info("💾 Armazenando no Supabase...")
            estatisticas_armazenamento = self.supabase_client.processar_intimacoes(intimacoes_processadas)
            
            # Atualizar relatório
            relatorio["total_novas"] = estatisticas_armazenamento["novas_inseridas"]
            relatorio["total_duplicadas"] = estatisticas_armazenamento["duplicatas_encontradas"]
            relatorio["total_erros"] += estatisticas_armazenamento["erros"]
            relatorio["detalhes_erros"].extend(estatisticas_armazenamento["detalhes_erros"])
            
            # Passo 4: Finalizar
            tempo_total = time.time() - inicio_execucao
            relatorio["tempo_execucao_segundos"] = int(tempo_total)
            relatorio["status_execucao"] = "sucesso"
            relatorio["fim_execucao"] = datetime.now().isoformat()
            
            self.logger.info("🎉 Extração concluída com sucesso!")
            self.logger.info(f"📊 Resumo: {relatorio['total_encontradas']} encontradas, "
                           f"{relatorio['total_novas']} novas, "
                           f"{relatorio['total_duplicadas']} duplicadas, "
                           f"{relatorio['total_erros']} erros")
            
        except Exception as e:
            # Erro geral na execução
            tempo_total = time.time() - inicio_execucao
            relatorio["tempo_execucao_segundos"] = int(tempo_total)
            relatorio["status_execucao"] = "erro"
            relatorio["erro_principal"] = str(e)
            relatorio["fim_execucao"] = datetime.now().isoformat()
            
            self.logger.error(f"❌ Erro na extração: {e}")
        
        finally:
            # Registrar log da execução
            try:
                self.supabase_client.registrar_log_execucao(relatorio)
            except Exception as e:
                self.logger.error(f"Erro ao registrar log: {e}")
        
        return relatorio
    
    def executar_recuperacao_historica(self, dias: int = 7) -> Dict:
        """
        Executa recuperação de dados históricos
        
        Args:
            dias: Número de dias para trás
            
        Returns:
            Dict: Relatório de recuperação
        """
        self.logger.info(f"📅 Iniciando recuperação histórica de {dias} dias")
        
        return self.executar_extracao_diaria()  # Usa a mesma lógica
    
    def obter_relatorio_status(self) -> Dict:
        """
        Obtém relatório de status completo do sistema
        
        Returns:
            Dict: Status completo
        """
        self.logger.info("📊 Gerando relatório de status...")
        
        try:
            # Testes dos componentes
            testes_componentes = self.testar_componentes()
            
            # Estatísticas da base
            estatisticas_base = self.supabase_client.obter_estatisticas_base()
            
            relatorio = {
                "timestamp": datetime.now().isoformat(),
                "componentes": testes_componentes,
                "estatisticas_base": estatisticas_base,
                "sistema_funcional": all(testes_componentes.values())
            }
            
            return relatorio
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "erro": str(e),
                "sistema_funcional": False
            }
    
    def executar_teste_completo(self) -> bool:
        """
        Executa teste completo do sistema
        
        Returns:
            bool: True se tudo funcionando
        """
        self.logger.info("🧪 Executando teste completo do sistema...")
        
        try:
            # Teste dos componentes
            testes = self.testar_componentes()
            
            if not all(testes.values()):
                self.logger.error("❌ Falha nos testes de componentes")
                return False
            
            # Teste de extração pequena (últimos 2 dias)
            self.logger.info("🔬 Testando extração de dados...")
            sucesso_api, dados = self.api_client.buscar_todas_oabs_eduardo()
            
            if not sucesso_api:
                self.logger.error("❌ Falha no teste de extração")
                return False
            
            # Testar processamento de pelo menos uma intimação
            if dados:
                primeira = dados[0]
                intimacao_processada = self.text_processor.processar_intimacao_completa(primeira)
                
                if not self.text_processor.validar_intimacao(intimacao_processada):
                    self.logger.error("❌ Falha na validação de intimação processada")
                    return False
            
            self.logger.info("✅ Teste completo: SUCESSO")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro no teste completo: {e}")
            return False