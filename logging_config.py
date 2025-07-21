"""
Configuração do sistema de logging
"""
import logging
import logging.handlers
import os
from datetime import datetime

from config import LOG_LEVEL, LOG_FILE

def setup_logging():
    """
    Configura o sistema de logging
    """
    # Criar diretório de logs se não existir
    log_dir = os.path.dirname(LOG_FILE) if os.path.dirname(LOG_FILE) else 'logs'
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar nível
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Formato das mensagens
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo (com rotação)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    
    # Configurar logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configurar logger específico do projeto
    logger = logging.getLogger('djen_extractor')
    logger.info(f"✅ Sistema de logging configurado - Nível: {LOG_LEVEL}")
    
    return logger

def get_logger(name: str):
    """
    Obtém um logger específico
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)