"""
Cliente Supabase para armazenamento das intimações do DJEN
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY, TABELA_INTIMACOES, TABELA_LOGS

class SupabaseClient:
    """
    Cliente para interagir com o Supabase
    """
    
    def __init__(self):
        self.url = SUPABASE_URL
        self.key = SUPABASE_KEY
        self.client: Optional[Client] = None
        self.logger = logging.getLogger(__name__)
        
        if not self.url or not self.key:
            raise ValueError("Configurações do Supabase não encontradas")
        
        self._conectar()
    
    def _conectar(self):
        """
        Estabelece conexão com o Supabase
        """
        try:
            self.client = create_client(self.url, self.key)
            self.logger.info("✅ Conexão com Supabase estabelecida")
        except Exception as e:
            self.logger.error(f"❌ Erro ao conectar com Supabase: {e}")
            raise
    
    def testar_conexao(self) -> bool:
        """
        Testa a conexão com o Supabase
        
        Returns:
            bool: True se conexão estiver funcionando
        """
        try:
            # Testar fazendo uma query simples na tabela de logs
            result = self.client.table(TABELA_LOGS).select("id").limit(1).execute()
            self.logger.info("✅ Teste de conexão Supabase: SUCESSO")
            return True
        except Exception as e:
            self.logger.error(f"❌ Teste de conexão Supabase falhou: {e}")
            return False
    
    def buscar_intimacoes(self, limite: int = 10, data_especifica: str = None) -> List[Dict]:
        """
        Busca intimações na base de dados
        
        Args:
            limite: Número máximo de intimações
            data_especifica: Filtrar por data específica (YYYY-MM-DD)
            
        Returns:
            List[Dict]: Lista de intimações
        """
        try:
            query = self.client.table(TABELA_INTIMACOES).select("*")
            
            if data_especifica:
                query = query.eq("data_publicacao", data_especifica)
            
            result = query.order("data_extracao", desc=True).limit(limite).execute()
            return result.data
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao buscar intimações: {e}")
            return []
    
    def obter_estatisticas_tribunal(self) -> List[Dict]:
        """
        Obtém estatísticas agrupadas por tribunal
        
        Returns:
            List[Dict]: Estatísticas por tribunal
        """
        try:
            # Buscar todos os tribunais
            result = self.client.table(TABELA_INTIMACOES).select("tribunal").execute()
            
            # Contar por tribunal
            tribunais = {}
            for row in result.data:
                tribunal = row.get('tribunal', 'N/A')
                tribunais[tribunal] = tribunais.get(tribunal, 0) + 1
            
            # Converter para lista ordenada
            stats = [
                {'tribunal': tribunal, 'total': total}
                for tribunal, total in sorted(tribunais.items(), key=lambda x: x[1], reverse=True)
            ]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter estatísticas por tribunal: {e}")
            return []
    
    def obter_estatisticas(self) -> Dict:
        """
        Obtém estatísticas gerais da base de dados
        
        Returns:
            Dict: Estatísticas gerais
        """
        try:
            # Total de intimações
            result_total = self.client.table(TABELA_INTIMACOES).select("id").execute()
            total_intimacoes = len(result_total.data)
            
            # Tribunais únicos
            result_tribunais = self.client.table(TABELA_INTIMACOES).select("tribunal").execute()
            tribunais_unicos = len(set(row.get('tribunal', 'N/A') for row in result_tribunais.data))
            
            return {
                'total_intimacoes': total_intimacoes,
                'tribunais_unicos': tribunais_unicos
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {
                'total_intimacoes': 0,
                'tribunais_unicos': 0
            }
    
    def obter_logs_execucao(self, limite: int = 10) -> List[Dict]:
        """
        Obtém logs de execução da base de dados
        
        Args:
            limite: Número máximo de logs
            
        Returns:
            List[Dict]: Lista de logs
        """
        try:
            result = self.client.table(TABELA_LOGS).select("*").order("data_extracao", desc=True).limit(limite).execute()
            return result.data
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter logs de execução: {e}")
            return []
    
    def verificar_duplicata(self, id_intimacao: str, hash_conteudo: Optional[str] = None) -> Tuple[bool, Optional[Dict]]:
        """
        Verifica se uma intimação já existe na base
        
        Args:
            id_intimacao: ID da intimação
            hash_conteudo: Hash do conteúdo (opcional)
            
        Returns:
            Tuple[bool, Optional[Dict]]: (existe, dados_existentes)
        """
        try:
            query = self.client.table(TABELA_INTIMACOES).select("*")
            
            # Buscar por ID
            query = query.eq("id_intimacao", id_intimacao)
            
            # Se tiver hash, buscar também por hash
            if hash_conteudo:
                query = query.or_(f"hash_conteudo.eq.{hash_conteudo}")
            
            result = query.limit(1).execute()
            
            if result.data:
                self.logger.info(f"Duplicata encontrada para intimação {id_intimacao}")
                return True, result.data[0]
            else:
                return False, None
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar duplicata: {e}")
            return False, None
    
    def inserir_intimacao(self, intimacao: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Insere uma nova intimação na base
        
        Args:
            intimacao: Dados da intimação processada
            
        Returns:
            Tuple[bool, Optional[Dict]]: (sucesso, dados_inseridos)
        """
        try:
            # Preparar dados para inserção
            dados_insercao = {
                "id_intimacao": intimacao["id_intimacao"],
                "numero_processo": intimacao.get("numero_processo"),
                "tribunal": intimacao.get("tribunal"),
                "orgao_julgador": intimacao.get("orgao_julgador"),
                "data_publicacao": intimacao.get("data_publicacao"),
                "tipo_comunicacao": intimacao.get("tipo_comunicacao"),
                "conteudo_texto": intimacao["conteudo_texto"],
                "conteudo_original": json.dumps(intimacao.get("conteudo_original", {}), ensure_ascii=False),
                "hash_conteudo": intimacao.get("hash_conteudo"),
                "metadados": json.dumps(intimacao.get("metadados", {}), ensure_ascii=False),
                "status_processamento": intimacao.get("status_processamento", "extraido"),
                "data_extracao": datetime.now().isoformat()
            }
            
            # Inserir na base
            result = self.client.table(TABELA_INTIMACOES).insert(dados_insercao).execute()
            
            if result.data:
                self.logger.info(f"✅ Intimação {intimacao['id_intimacao']} inserida com sucesso")
                return True, result.data[0]
            else:
                self.logger.error(f"❌ Falha ao inserir intimação {intimacao['id_intimacao']}")
                return False, None
                
        except Exception as e:
            self.logger.error(f"Erro ao inserir intimação: {e}")
            return False, None
    
    def processar_intimacoes(self, intimacoes: List[Dict]) -> Dict:
        """
        Processa uma lista de intimações, verificando duplicatas e inserindo novas
        
        Args:
            intimacoes: Lista de intimações processadas
            
        Returns:
            Dict: Estatísticas do processamento
        """
        estatisticas = {
            "total_processadas": len(intimacoes),
            "novas_inseridas": 0,
            "duplicatas_encontradas": 0,
            "erros": 0,
            "detalhes_erros": []
        }
        
        self.logger.info(f"Processando {len(intimacoes)} intimações")
        
        for intimacao in intimacoes:
            try:
                id_intimacao = intimacao["id_intimacao"]
                hash_conteudo = intimacao.get("hash_conteudo")
                
                # Verificar duplicata
                existe, dados_existentes = self.verificar_duplicata(id_intimacao, hash_conteudo)
                
                if existe:
                    estatisticas["duplicatas_encontradas"] += 1
                    self.logger.info(f"Duplicata: {id_intimacao}")
                else:
                    # Inserir nova intimação
                    sucesso, dados_inseridos = self.inserir_intimacao(intimacao)
                    
                    if sucesso:
                        estatisticas["novas_inseridas"] += 1
                    else:
                        estatisticas["erros"] += 1
                        estatisticas["detalhes_erros"].append(f"Erro ao inserir {id_intimacao}")
                
            except Exception as e:
                estatisticas["erros"] += 1
                erro_msg = f"Erro ao processar intimação: {e}"
                estatisticas["detalhes_erros"].append(erro_msg)
                self.logger.error(erro_msg)
        
        self.logger.info(f"Processamento concluído: {estatisticas['novas_inseridas']} inseridas, "
                        f"{estatisticas['duplicatas_encontradas']} duplicatas, "
                        f"{estatisticas['erros']} erros")
        
        return estatisticas
    
    def registrar_log_execucao(self, log_dados: Dict) -> bool:
        """
        Registra um log de execução
        
        Args:
            log_dados: Dados do log de execução
            
        Returns:
            bool: True se inserido com sucesso
        """
        try:
            # Preparar dados do log
            dados_log = {
                "total_encontradas": log_dados.get("total_encontradas", 0),
                "total_novas": log_dados.get("total_novas", 0),
                "total_duplicadas": log_dados.get("total_duplicadas", 0),
                "status_execucao": log_dados.get("status_execucao", "sucesso"),
                "erro_detalhes": log_dados.get("erro_detalhes"),
                "tempo_execucao_segundos": log_dados.get("tempo_execucao_segundos", 0),
                "parametros_busca": json.dumps(log_dados.get("parametros_busca", {}), ensure_ascii=False),
                "response_api": json.dumps(log_dados.get("response_api", {}), ensure_ascii=False),
                "data_extracao": datetime.now().isoformat()
            }
            
            result = self.client.table(TABELA_LOGS).insert(dados_log).execute()
            
            if result.data:
                self.logger.info("✅ Log de execução registrado")
                return True
            else:
                self.logger.error("❌ Falha ao registrar log")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao registrar log: {e}")
            return False
    
    def obter_estatisticas_base(self) -> Dict:
        """
        Obtém estatísticas gerais da base de dados
        
        Returns:
            Dict: Estatísticas da base
        """
        try:
            # Total de intimações
            total_intimacoes = self.client.table(TABELA_INTIMACOES).select("id", count="exact").execute()
            
            # Total por tribunal
            tribunais = self.client.table(TABELA_INTIMACOES).select("tribunal").execute()
            
            # Últimas execuções
            ultimas_execucoes = self.client.table(TABELA_LOGS)\
                .select("*")\
                .order("data_extracao", desc=True)\
                .limit(5)\
                .execute()
            
            # Contar por tribunal
            tribunais_count = {}
            if tribunais.data:
                for item in tribunais.data:
                    tribunal = item.get("tribunal", "N/A")
                    tribunais_count[tribunal] = tribunais_count.get(tribunal, 0) + 1
            
            estatisticas = {
                "total_intimacoes": total_intimacoes.count if hasattr(total_intimacoes, 'count') else 0,
                "tribunais_ativos": tribunais_count,
                "ultimas_execucoes": ultimas_execucoes.data if ultimas_execucoes.data else []
            }
            
            return estatisticas
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def limpar_dados_teste(self) -> bool:
        """
        Remove todos os dados de teste (USE COM CUIDADO!)
        
        Returns:
            bool: True se limpeza foi bem-sucedida
        """
        try:
            # Confirmar que é ambiente de teste
            if "test" not in self.url.lower():
                self.logger.error("❌ Operação de limpeza bloqueada - não parece ser ambiente de teste")
                return False
            
            # Limpar tabelas
            self.client.table(TABELA_INTIMACOES).delete().neq("id", "").execute()
            self.client.table(TABELA_LOGS).delete().neq("id", "").execute()
            
            self.logger.warning("⚠️ Dados de teste removidos")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar dados: {e}")
            return False