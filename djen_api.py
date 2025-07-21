"""
Classe para consulta da API DJEN (Diário de Justiça Eletrônico Nacional)
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

from config import (
    DJEN_API_URL, DEFAULT_HEADERS, TIMEOUT_REQUESTS, ITEMS_POR_PAGINA,
    ADVOGADO_NOME, REGISTROS_OAB, DIAS_BUSCA
)

class DJENApiClient:
    """
    Cliente para interagir com a API DJEN
    """
    
    def __init__(self):
        self.api_url = DJEN_API_URL
        self.headers = DEFAULT_HEADERS.copy()
        self.timeout = TIMEOUT_REQUESTS
        self.logger = logging.getLogger(__name__)
    
    def _fazer_requisicao(self, params: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Faz uma requisição para a API DJEN
        
        Args:
            params: Parâmetros da requisição
            
        Returns:
            Tuple[bool, Optional[Dict]]: (sucesso, dados)
        """
        try:
            self.logger.info(f"Fazendo requisição para API DJEN: {params}")
            
            response = requests.get(
                self.api_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            
            self.logger.info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar se a resposta tem a estrutura esperada
                if 'status' in data and data['status'] == 'success':
                    self.logger.info(f"Requisição bem-sucedida. Count: {data.get('count', 0)}")
                    return True, data
                else:
                    self.logger.warning(f"Resposta com status não esperado: {data.get('status')}")
                    return False, data
                    
            else:
                self.logger.error(f"Erro na requisição: {response.status_code} - {response.text}")
                return False, None
                
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout na requisição após {self.timeout}s")
            return False, None
            
        except requests.exceptions.ConnectionError:
            self.logger.error("Erro de conexão com a API DJEN")
            return False, None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro na requisição: {e}")
            return False, None
            
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False, None
    
    def buscar_por_nome(
        self, 
        nome: str = ADVOGADO_NOME,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        pagina: int = 1
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Busca intimações por nome do advogado
        
        Args:
            nome: Nome do advogado
            data_inicio: Data início (yyyy-mm-dd)
            data_fim: Data fim (yyyy-mm-dd)
            pagina: Número da página
            
        Returns:
            Tuple[bool, Optional[Dict]]: (sucesso, dados)
        """
        # Se não informadas, usar período padrão (ontem até hoje)
        if not data_inicio or not data_fim:
            hoje = datetime.now().date()
            ontem = hoje - timedelta(days=DIAS_BUSCA)
            data_inicio = ontem.strftime("%Y-%m-%d")
            data_fim = hoje.strftime("%Y-%m-%d")
        
        params = {
            "nomeAdvogado": nome,
            "dataDisponibilizacaoInicio": data_inicio,
            "dataDisponibilizacaoFim": data_fim,
            "itensPorPagina": ITEMS_POR_PAGINA,
            "meio": "D",  # Diário Eletrônico
            "pagina": pagina
        }
        
        return self._fazer_requisicao(params)
    
    def buscar_por_oab(
        self,
        numero_oab: str,
        uf_oab: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        pagina: int = 1
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Busca intimações por número OAB
        
        Args:
            numero_oab: Número da OAB
            uf_oab: UF da OAB
            data_inicio: Data início (yyyy-mm-dd)
            data_fim: Data fim (yyyy-mm-dd)
            pagina: Número da página
            
        Returns:
            Tuple[bool, Optional[Dict]]: (sucesso, dados)
        """
        # Se não informadas, usar período padrão
        if not data_inicio or not data_fim:
            hoje = datetime.now().date()
            ontem = hoje - timedelta(days=DIAS_BUSCA)
            data_inicio = ontem.strftime("%Y-%m-%d")
            data_fim = hoje.strftime("%Y-%m-%d")
        
        params = {
            "numeroOab": numero_oab,
            "ufOab": uf_oab,
            "dataDisponibilizacaoInicio": data_inicio,
            "dataDisponibilizacaoFim": data_fim,
            "itensPorPagina": ITEMS_POR_PAGINA,
            "meio": "D",
            "pagina": pagina
        }
        
        return self._fazer_requisicao(params)
    
    def buscar_todas_oabs_eduardo(
        self,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> Tuple[bool, List[Dict]]:
        """
        Busca intimações em todos os registros OAB do Eduardo Koetz
        
        Args:
            data_inicio: Data início (yyyy-mm-dd)
            data_fim: Data fim (yyyy-mm-dd)
            
        Returns:
            Tuple[bool, List[Dict]]: (sucesso, lista de todas as intimações)
        """
        todas_intimacoes = []
        sucesso_geral = True
        
        self.logger.info(f"Buscando em {len(REGISTROS_OAB)} registros OAB do Eduardo Koetz")
        
        # Buscar por nome primeiro
        sucesso, dados = self.buscar_por_nome(data_inicio=data_inicio, data_fim=data_fim)
        if sucesso and dados and dados.get('items'):
            todas_intimacoes.extend(dados['items'])
            self.logger.info(f"Encontradas {len(dados['items'])} intimações por nome")
        elif not sucesso:
            sucesso_geral = False
            self.logger.warning("Falha na busca por nome")
        
        # Buscar por cada registro OAB
        for registro in REGISTROS_OAB:
            sucesso, dados = self.buscar_por_oab(
                numero_oab=registro["numero"],
                uf_oab=registro["uf"],
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            
            if sucesso and dados and dados.get('items'):
                # Adicionar items que ainda não estão na lista (deduplicação básica por ID)
                ids_existentes = {item['id'] for item in todas_intimacoes}
                novos_items = [item for item in dados['items'] if item['id'] not in ids_existentes]
                
                todas_intimacoes.extend(novos_items)
                self.logger.info(f"OAB {registro['numero']}/{registro['uf']}: "
                               f"{len(dados['items'])} total, {len(novos_items)} novos")
            elif not sucesso:
                sucesso_geral = False
                self.logger.warning(f"Falha na busca por OAB {registro['numero']}/{registro['uf']}")
        
        self.logger.info(f"Total de intimações únicas encontradas: {len(todas_intimacoes)}")
        return sucesso_geral, todas_intimacoes
    
    def buscar_periodo_extendido(
        self,
        dias: int = 7
    ) -> Tuple[bool, List[Dict]]:
        """
        Busca intimações em um período extendido (útil para recuperar dados)
        
        Args:
            dias: Número de dias para trás
            
        Returns:
            Tuple[bool, List[Dict]]: (sucesso, lista de intimações)
        """
        hoje = datetime.now().date()
        inicio = hoje - timedelta(days=dias)
        
        self.logger.info(f"Buscando intimações dos últimos {dias} dias ({inicio} até {hoje})")
        
        return self.buscar_todas_oabs_eduardo(
            data_inicio=inicio.strftime("%Y-%m-%d"),
            data_fim=hoje.strftime("%Y-%m-%d")
        )
    
    def testar_conectividade(self) -> bool:
        """
        Testa a conectividade com a API
        
        Returns:
            bool: True se conseguir conectar
        """
        try:
            # Fazer uma busca simples dos últimos 2 dias
            sucesso, dados = self.buscar_por_nome()
            
            if sucesso:
                self.logger.info("✅ Teste de conectividade: SUCESSO")
                return True
            else:
                self.logger.error("❌ Teste de conectividade: FALHA")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro no teste de conectividade: {e}")
            return False