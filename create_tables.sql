-- Script SQL para criar as tabelas no Supabase
-- Execute este script no SQL Editor do Supabase

-- Tabela principal para armazenar as intimações do Eduardo Koetz
CREATE TABLE IF NOT EXISTS intimacoes_eduardo_koetz (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  id_intimacao VARCHAR(255) UNIQUE NOT NULL, -- ID da API
  numero_processo VARCHAR(50),
  tribunal VARCHAR(100),
  orgao_julgador VARCHAR(255),
  data_publicacao DATE,
  tipo_comunicacao VARCHAR(100),
  data_extracao TIMESTAMP DEFAULT NOW(),
  conteudo_texto TEXT NOT NULL, -- Texto limpo e legível
  conteudo_original JSONB, -- JSON completo da API
  hash_conteudo VARCHAR(255) UNIQUE, -- Hash da API para deduplicação
  metadados JSONB, -- Dados extras (destinatários, links, etc.)
  status_processamento VARCHAR(50) DEFAULT 'extraido'
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_hash_conteudo ON intimacoes_eduardo_koetz(hash_conteudo);
CREATE INDEX IF NOT EXISTS idx_data_publicacao ON intimacoes_eduardo_koetz(data_publicacao);
CREATE INDEX IF NOT EXISTS idx_data_extracao ON intimacoes_eduardo_koetz(data_extracao);
CREATE INDEX IF NOT EXISTS idx_tribunal ON intimacoes_eduardo_koetz(tribunal);
CREATE INDEX IF NOT EXISTS idx_id_intimacao ON intimacoes_eduardo_koetz(id_intimacao);

-- Tabela de logs das execuções
CREATE TABLE IF NOT EXISTS logs_extracao_djen (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  data_extracao TIMESTAMP DEFAULT NOW(),
  total_encontradas INTEGER DEFAULT 0,
  total_novas INTEGER DEFAULT 0,
  total_duplicadas INTEGER DEFAULT 0,
  status_execucao VARCHAR(50), -- 'sucesso', 'erro', 'parcial'
  erro_detalhes TEXT,
  tempo_execucao_segundos INTEGER,
  parametros_busca JSONB,
  response_api JSONB -- Resposta completa da API para debug
);

-- Índices para a tabela de logs
CREATE INDEX IF NOT EXISTS idx_logs_data_extracao ON logs_extracao_djen(data_extracao);
CREATE INDEX IF NOT EXISTS idx_logs_status ON logs_extracao_djen(status_execucao);

-- Comentários nas tabelas
COMMENT ON TABLE intimacoes_eduardo_koetz IS 'Tabela principal para armazenar as intimações do Eduardo Koetz extraídas do DJEN';
COMMENT ON TABLE logs_extracao_djen IS 'Log de execuções do sistema de extração DJEN';

-- Comentários nas colunas principais
COMMENT ON COLUMN intimacoes_eduardo_koetz.id_intimacao IS 'ID único da intimação na API DJEN';
COMMENT ON COLUMN intimacoes_eduardo_koetz.hash_conteudo IS 'Hash do conteúdo para deduplicação';
COMMENT ON COLUMN intimacoes_eduardo_koetz.conteudo_texto IS 'Texto da intimação limpo e formatado';
COMMENT ON COLUMN intimacoes_eduardo_koetz.conteudo_original IS 'JSON completo retornado pela API';
COMMENT ON COLUMN intimacoes_eduardo_koetz.metadados IS 'Metadados estruturados extraídos';

-- Inserir registro inicial para teste
INSERT INTO logs_extracao_djen (
  total_encontradas,
  total_novas, 
  total_duplicadas,
  status_execucao,
  tempo_execucao_segundos,
  parametros_busca
) VALUES (
  0,
  0,
  0,
  'sistema_criado',
  0,
  '{"evento": "criacao_tabelas", "versao": "1.0"}'
) ON CONFLICT DO NOTHING;

-- Verificar se as tabelas foram criadas corretamente
SELECT 
  schemaname,
  tablename,
  tableowner,
  hasindexes,
  hasrules,
  hastriggers
FROM pg_tables 
WHERE tablename IN ('intimacoes_eduardo_koetz', 'logs_extracao_djen');

-- Verificar índices criados
SELECT 
  indexname,
  tablename,
  indexdef
FROM pg_indexes 
WHERE tablename IN ('intimacoes_eduardo_koetz', 'logs_extracao_djen')
ORDER BY tablename, indexname;