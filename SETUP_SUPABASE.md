# 🗄️ Setup do Supabase

Este documento explica como configurar o banco de dados Supabase para o sistema DJEN.

## 📋 **Configuração Rápida**

### 1. **Criar Projeto no Supabase**
1. Acesse https://supabase.com
2. Crie uma conta (se não tiver)
3. Clique em "New Project"
4. Defina nome, senha e região

### 2. **Obter Credenciais**
1. No painel do projeto, vá em **Settings > API**
2. Copie a **URL** e a **anon public key**
3. Configure no arquivo `.env`:

```env
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_KEY=eyJhbGciOi...sua_chave_aqui
```

### 3. **Criar Tabelas**

Execute o script SQL no **SQL Editor** do Supabase:

#### **Tabela Principal: intimacoes_djen**
```sql
CREATE TABLE intimacoes_djen (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    id_intimacao TEXT UNIQUE NOT NULL,
    numero_processo TEXT,
    tribunal TEXT,
    orgao_julgador TEXT,
    data_publicacao DATE,
    tipo_comunicacao TEXT,
    conteudo_texto TEXT NOT NULL,
    data_extracao TIMESTAMPTZ DEFAULT NOW(),
    hash_conteudo TEXT,
    metadados JSONB,
    conteudo_original JSONB,
    status_processamento TEXT DEFAULT 'extraido',
    tipo_documento TEXT,
    
    CONSTRAINT unique_intimacao UNIQUE (id_intimacao)
);

-- Índices para performance
CREATE INDEX idx_intimacoes_data_publicacao ON intimacoes_djen(data_publicacao);
CREATE INDEX idx_intimacoes_tribunal ON intimacoes_djen(tribunal);
CREATE INDEX idx_intimacoes_data_extracao ON intimacoes_djen(data_extracao);
CREATE INDEX idx_intimacoes_status ON intimacoes_djen(status_processamento);
```

#### **Tabela de Logs: logs_execucao**
```sql
CREATE TABLE logs_execucao (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    total_encontradas INTEGER DEFAULT 0,
    total_novas INTEGER DEFAULT 0,
    total_duplicadas INTEGER DEFAULT 0,
    status_execucao TEXT DEFAULT 'sucesso',
    data_extracao TIMESTAMPTZ DEFAULT NOW(),
    tempo_execucao_segundos NUMERIC,
    erro_detalhes TEXT,
    parametros_busca JSONB,
    response_api JSONB
);

-- Índice para logs
CREATE INDEX idx_logs_data_extracao ON logs_execucao(data_extracao);
CREATE INDEX idx_logs_status ON logs_execucao(status_execucao);
```

### 4. **Configurar RLS (Row Level Security)**

**Opcional**: Para segurança adicional, configure políticas:

```sql
-- Habilitar RLS
ALTER TABLE intimacoes_djen ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs_execucao ENABLE ROW LEVEL SECURITY;

-- Política para leitura pública (para testes)
CREATE POLICY "Public Access" ON intimacoes_djen FOR ALL TO anon USING (true);
CREATE POLICY "Public Access" ON logs_execucao FOR ALL TO anon USING (true);
```

## ✅ **Verificação**

Após criar as tabelas, teste a conexão:

```bash
# No terminal do projeto:
python -c "
from supabase_client import SupabaseClient
client = SupabaseClient()
print('✅ Conexão OK!' if client.testar_conexao() else '❌ Erro na conexão')
"
```

## 📊 **Estrutura de Dados**

### **intimacoes_djen**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Chave primária |
| `id_intimacao` | TEXT | ID único da intimação (evita duplicatas) |
| `numero_processo` | TEXT | Número do processo |
| `tribunal` | TEXT | Tribunal (TJSP, TRF4, etc.) |
| `orgao_julgador` | TEXT | Vara/Órgão responsável |
| `data_publicacao` | DATE | Data de publicação no DJEN |
| `tipo_comunicacao` | TEXT | Tipo (Intimação, Citação, etc.) |
| `conteudo_texto` | TEXT | **Texto limpo e legível** |
| `data_extracao` | TIMESTAMPTZ | **Timestamp da extração** |
| `hash_conteudo` | TEXT | Hash para verificação |
| `metadados` | JSONB | Dados extras da API |
| `conteudo_original` | JSONB | Resposta original da API |
| `status_processamento` | TEXT | Status do processamento |

### **logs_execucao**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Chave primária |
| `total_encontradas` | INTEGER | Total encontrado na API |
| `total_novas` | INTEGER | Novas inseridas |
| `total_duplicadas` | INTEGER | Duplicatas ignoradas |
| `status_execucao` | TEXT | sucesso/erro |
| `data_extracao` | TIMESTAMPTZ | Timestamp da execução |
| `tempo_execucao_segundos` | NUMERIC | Tempo gasto |
| `erro_detalhes` | TEXT | Detalhes de erro |
| `parametros_busca` | JSONB | Parâmetros usados |
| `response_api` | JSONB | Resposta da API |

## 🔧 **Troubleshooting**

### **Erro de Conexão**
1. Verifique URL e KEY no `.env`
2. Teste conectividade: `curl https://sua-url.supabase.co/rest/v1/`

### **Erro de Permissão**
1. Verifique se RLS está configurado corretamente
2. Use a chave `service_role` se necessário (não recomendado para produção)

### **Tabelas não Criadas**
1. Execute o SQL no **SQL Editor** do Supabase
2. Verifique se não há erros de sintaxe
3. Confirme na aba **Table Editor**

## 📞 **Suporte**

Para dúvidas específicas sobre Supabase:
- Documentação: https://supabase.com/docs
- Dashboard: https://supabase.com/dashboard

**O sistema está configurado para funcionar com essas tabelas imediatamente após a criação!**