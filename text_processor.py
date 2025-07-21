"""
Sistema de processamento de texto para intimações do DJEN
"""
import re
import logging
from html import unescape
from typing import Dict, Optional
from datetime import datetime

class TextProcessor:
    """
    Classe para processar e limpar o texto das intimações
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def processar_texto(self, texto: str) -> str:
        """
        Processa o texto HTML das intimações para formato limpo e legível
        Baseado na lógica do workflow N8N original
        
        Args:
            texto: Texto original da intimação (pode conter HTML)
            
        Returns:
            str: Texto limpo e legível
        """
        if not texto:
            return ''
        
        try:
            limpo = texto
            
            # Remove tags HTML mas preserva estrutura
            limpo = re.sub(r'<br\s*/?>', '\n', limpo, flags=re.IGNORECASE)
            limpo = re.sub(r'</p>', '\n\n', limpo, flags=re.IGNORECASE)
            limpo = re.sub(r'<p[^>]*>', '', limpo, flags=re.IGNORECASE)
            limpo = re.sub(r'<div[^>]*>', '\n', limpo, flags=re.IGNORECASE)
            limpo = re.sub(r'</div>', '', limpo, flags=re.IGNORECASE)
            limpo = re.sub(r'<[^>]*>', '', limpo)  # Remove todas as outras tags HTML
            
            # Decodifica entidades HTML
            limpo = unescape(limpo)
            limpo = limpo.replace('&nbsp;', ' ')
            limpo = limpo.replace('&amp;', '&')
            limpo = limpo.replace('&lt;', '<')
            limpo = limpo.replace('&gt;', '>')
            limpo = limpo.replace('&quot;', '"')
            limpo = limpo.replace('&#39;', "'")
            
            # Normaliza quebras de linha
            limpo = limpo.replace('\r\n', '\n')
            limpo = limpo.replace('\r', '\n')
            
            # Remove espaços extras mas mantém estrutura
            limpo = re.sub(r'[ \t]+', ' ', limpo)
            limpo = re.sub(r'\n[ \t]+', '\n', limpo)
            limpo = re.sub(r'[ \t]+\n', '\n', limpo)
            
            # Normaliza múltiplas quebras
            limpo = re.sub(r'\n{3,}', '\n\n', limpo)
            
            # Remove espaços do início e fim
            limpo = limpo.strip()
            
            return limpo
            
        except Exception as e:
            self.logger.error(f"Erro ao processar texto: {e}")
            return texto  # Retorna original em caso de erro
    
    def extrair_metadados_texto(self, texto: str) -> Dict:
        """
        Extrai metadados úteis do texto da intimação
        
        Args:
            texto: Texto processado da intimação
            
        Returns:
            Dict: Metadados extraídos
        """
        metadados = {}
        
        try:
            # Extrair número do processo (formato padrão)
            processo_match = re.search(r'(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4})', texto)
            if processo_match:
                metadados['numero_processo_extraido'] = processo_match.group(1)
            
            # Extrair data de assinatura eletrônica
            data_match = re.search(r'data da assinatura eletrônica\.?', texto, re.IGNORECASE)
            if data_match:
                metadados['tem_assinatura_eletronica'] = True
            
            # Extrair tipo de documento comum (despacho, sentença, etc.)
            if re.search(r'\bDESPACHO\b', texto, re.IGNORECASE):
                metadados['tipo_documento_extraido'] = 'Despacho'
            elif re.search(r'\bSENTENÇA\b', texto, re.IGNORECASE):
                metadados['tipo_documento_extraido'] = 'Sentença'
            elif re.search(r'\bDECISÃO\b', texto, re.IGNORECASE):
                metadados['tipo_documento_extraido'] = 'Decisão'
            elif re.search(r'\bACÓRDÃO\b', texto, re.IGNORECASE):
                metadados['tipo_documento_extraido'] = 'Acórdão'
            
            # Extrair informações de prazo
            prazo_matches = re.findall(r'prazo de (\d+) \(([^)]+)\) dias?', texto, re.IGNORECASE)
            if prazo_matches:
                metadados['prazos_encontrados'] = prazo_matches
            
            # Verificar se é intimação de advogado específico
            if 'EDUARDO KOETZ' in texto.upper():
                metadados['eduardo_koetz_mencionado'] = True
            
            # Contar linhas e caracteres
            metadados['total_linhas'] = len(texto.split('\n'))
            metadados['total_caracteres'] = len(texto)
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair metadados: {e}")
        
        return metadados
    
    def processar_intimacao_completa(self, item_api: Dict) -> Dict:
        """
        Processa uma intimação completa da API, incluindo texto e metadados
        
        Args:
            item_api: Item da resposta da API DJEN
            
        Returns:
            Dict: Intimação processada com todos os dados limpos
        """
        try:
            # Processar o texto
            texto_original = item_api.get('texto', '')
            texto_limpo = self.processar_texto(texto_original)
            
            # Extrair metadados do texto
            metadados_texto = self.extrair_metadados_texto(texto_limpo)
            
            # Construir objeto processado
            intimacao_processada = {
                # IDs e controle
                'id_intimacao': str(item_api.get('id', '')),
                'hash_conteudo': item_api.get('hash', ''),
                
                # Dados principais
                'numero_processo': item_api.get('numero_processo') or item_api.get('numeroprocessocommascara', ''),
                'tribunal': item_api.get('siglaTribunal', ''),
                'orgao_julgador': item_api.get('nomeOrgao', ''),
                'tipo_comunicacao': item_api.get('tipoComunicacao', ''),
                'tipo_documento': item_api.get('tipoDocumento', ''),
                
                # Datas
                'data_publicacao': self._processar_data(item_api.get('data_disponibilizacao')),
                'data_extracao': datetime.now(),
                
                # Conteúdo
                'conteudo_texto': texto_limpo,
                'conteudo_original': item_api,
                
                # Metadados estruturados
                'metadados': {
                    'numero_comunicacao': item_api.get('numeroComunicacao'),
                    'classe': item_api.get('nomeClasse'),
                    'codigo_classe': item_api.get('codigoClasse'),
                    'link': item_api.get('link'),
                    'meio_completo': item_api.get('meiocompleto'),
                    'status': item_api.get('status'),
                    'ativo': item_api.get('ativo'),
                    'destinatarios': item_api.get('destinatarios', []),
                    'advogados_destinatarios': item_api.get('destinatarioadvogados', []),
                    'metadados_texto': metadados_texto
                },
                
                # Status de processamento
                'status_processamento': 'extraido'
            }
            
            return intimacao_processada
            
        except Exception as e:
            self.logger.error(f"Erro ao processar intimação completa: {e}")
            # Retornar estrutura mínima em caso de erro
            return {
                'id_intimacao': str(item_api.get('id', '')),
                'hash_conteudo': item_api.get('hash', ''),
                'conteudo_texto': item_api.get('texto', ''),
                'conteudo_original': item_api,
                'status_processamento': 'erro_processamento',
                'erro_processamento': str(e)
            }
    
    def _processar_data(self, data_str: Optional[str]) -> Optional[str]:
        """
        Processa uma string de data para formato padrão
        
        Args:
            data_str: String de data da API
            
        Returns:
            Optional[str]: Data em formato ISO (YYYY-MM-DD) ou None
        """
        if not data_str:
            return None
        
        try:
            # Se já está no formato ISO (YYYY-MM-DD)
            if re.match(r'^\d{4}-\d{2}-\d{2}', data_str):
                return data_str.split('T')[0]  # Remove parte de tempo se houver
            
            # Se está no formato brasileiro (DD/MM/YYYY)
            if re.match(r'^\d{2}/\d{2}/\d{4}', data_str):
                dia, mes, ano = data_str.split('/')[0:3]
                return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
            
            # Outros formatos podem ser adicionados aqui
            return None
            
        except Exception as e:
            self.logger.warning(f"Erro ao processar data '{data_str}': {e}")
            return None
    
    def eh_eduardo_unico_advogado(self, texto: str, metadados: Dict = None) -> bool:
        """
        Verifica se Eduardo Koetz é o único advogado mencionado na intimação
        
        Args:
            texto: Texto da intimação
            metadados: Metadados opcionais com dados de advogados
            
        Returns:
            bool: True se Eduardo for o único advogado
        """
        try:
            # Normalizar texto para busca
            texto_upper = texto.upper()
            
            # Verificar se Eduardo Koetz está mencionado
            eduardo_presente = 'EDUARDO KOETZ' in texto_upper
            
            if not eduardo_presente:
                return False
            
            # Buscar padrões de listagem de advogados
            # Padrão 1: "ADV: NOME1, NOME2, ..."
            # Padrão 2: "ADVOGADO(A): NOME"
            match_advogados = re.search(r'ADV(?:OGAD[OA]?)?\s*(?:\([^\)]*\))?\s*:\s*(.+?)(?=\n|$)', texto_upper)
            
            if not match_advogados:
                # Se não encontrou padrão de lista de advogados, assumir que Eduardo é único
                return True
                
            lista_advogados = match_advogados.group(1)
            
            # Dividir por vírgulas para separar os advogados
            advogados_individuais = lista_advogados.split(',')
            
            # Limpar cada nome de advogado
            nomes_advogados = []
            for advogado in advogados_individuais:
                # Remover informações de OAB
                nome_limpo = re.sub(r'\([^)]*\)', '', advogado).strip()
                nome_limpo = re.sub(r'OAB\s*[^\s,]+', '', nome_limpo).strip()
                
                # Filtrar apenas se parecer um nome próprio
                if len(nome_limpo) > 5:
                    palavras = nome_limpo.split()
                    # Remover palavras comuns
                    palavras_filtradas = [p for p in palavras if p not in ['E', 'DA', 'DE', 'DO', 'DOS', 'DAS']]
                    
                    if len(palavras_filtradas) >= 2:  # Pelo menos nome e sobrenome
                        nome_final = ' '.join(palavras_filtradas).strip()
                        if nome_final:
                            nomes_advogados.append(nome_final)
            
            # Contar quantos advogados diferentes de Eduardo foram encontrados
            outros_advogados = []
            for nome in nomes_advogados:
                # Verificar se não é Eduardo Koetz (tem que ter tanto EDUARDO quanto KOETZ para ser considerado Eduardo)
                if not ('EDUARDO' in nome and 'KOETZ' in nome):
                    outros_advogados.append(nome)
            
            # Debug log
            self.logger.debug(f"Advogados encontrados: {nomes_advogados}")
            self.logger.debug(f"Outros advogados (não Eduardo): {outros_advogados}")
            
            # Eduardo é único se não há outros advogados mencionados
            is_unico = len(outros_advogados) == 0 and eduardo_presente
            
            return is_unico
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar advogado único: {e}")
            return False
    
    def validar_intimacao(self, intimacao: Dict) -> bool:
        """
        Valida se uma intimação processada está válida
        
        Args:
            intimacao: Intimação processada
            
        Returns:
            bool: True se válida
        """
        try:
            # Verificações obrigatórias
            if not intimacao.get('id_intimacao'):
                self.logger.warning("Intimação sem ID")
                return False
            
            if not intimacao.get('conteudo_texto'):
                self.logger.warning(f"Intimação {intimacao['id_intimacao']} sem texto")
                return False
            
            # Verificações de qualidade
            texto = intimacao['conteudo_texto']
            if len(texto) < 50:  # Texto muito pequeno
                self.logger.warning(f"Intimação {intimacao['id_intimacao']} com texto muito pequeno")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao validar intimação: {e}")
            return False