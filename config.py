"""
Configurações do sistema de extração DJEN
"""
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações da API DJEN
DJEN_API_URL = os.getenv('DJEN_API_URL', 'https://comunicaapi.pje.jus.br/api/v1/comunicacao')
TIMEOUT_REQUESTS = int(os.getenv('TIMEOUT_REQUESTS', '30'))
ITEMS_POR_PAGINA = int(os.getenv('ITEMS_POR_PAGINA', '100'))
DIAS_BUSCA = int(os.getenv('DIAS_BUSCA', '1'))

# Configurações do Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Dados do advogado Eduardo Koetz
ADVOGADO_NOME = os.getenv('ADVOGADO_NOME', 'Eduardo Koetz')
ADVOGADO_OAB_PRINCIPAL = os.getenv('ADVOGADO_OAB_PRINCIPAL', '73409')
ADVOGADO_UF_PRINCIPAL = os.getenv('ADVOGADO_UF_PRINCIPAL', 'RS')

# Registros OAB do Eduardo Koetz
REGISTROS_OAB = [
    {"numero": "42934", "uf": "SC"},
    {"numero": "73409", "uf": "RS"},  # Principal
    {"numero": "72951", "uf": "PR"},
    {"numero": "435266", "uf": "SP"},
    {"numero": "204531", "uf": "MG"}
]

# Configurações de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'djen_extractor.log')

# Headers para requisições
DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "ADVBOX-DJEN-Extractor/1.0",
    "Content-Type": "application/json"
}

# Configurações das tabelas
TABELA_INTIMACOES = 'intimacoes_eduardo_koetz'
TABELA_LOGS = 'logs_extracao_djen'

# Validação de configurações obrigatórias
def validar_configuracoes():
    """
    Valida se as configurações obrigatórias estão presentes
    """
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL não configurada")
    if not SUPABASE_KEY:
        raise ValueError("SUPABASE_KEY não configurada")
    
    return True